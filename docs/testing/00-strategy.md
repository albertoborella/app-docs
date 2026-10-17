# Estrategia de pruebas

Estrategia de verificación del Gestor de documentación oficial láctea, derivada de `design.md` (Testing Strategy) y del desglose de tareas (`tasks.md`). El objetivo: probar la **especificación**, no la implementación accidental — cada regla de negocio y cada escenario de spec deben tener su prueba.

## Niveles

| Nivel | Qué cubre | Enfoque |
| --- | --- | --- |
| Unidad | Lógica de hash/tokens; reglas de borrado suave, control de roles, lista de formatos permitidos | pytest + SQLite temporal |
| Integración | 401 anónimo en toda la superficie; 403 de usuario normal en cada ruta de administrador; login/desactivación/reactivación; rechazos de tamaño y tipo en subida; autorización de descarga incluido 404 en documento borrado | FastAPI TestClient + almacenamiento temporal |
| CLI | `create-admin` crea un administrador hasheado con bcrypt en base vacía; se niega con un administrador existente sin `--force`; la contraseña nunca aparece en argv ni en logs | pytest + SQLite temporal, `getpass` simulado |
| Cliente de UI | Contrato de `api_client` (login, filtros, subida, descarga) | pytest con httpx simulado |
| E2E / manual | Humo de los tres objetivos (montaje web, `flet run` escritorio, `flet build` móvil); revisión de rendimiento de búsqueda con volumen sembrado | spike + nota en el reporte de verificación |

## Herramientas

| Herramienta | Uso |
| --- | --- |
| pytest | Ejecutor de pruebas (unitarias, integración, CLI, contrato) |
| FastAPI TestClient | Pruebas de la superficie HTTP sin servidor externo |
| SQLite temporal / `tmp` storage | Aislamiento por prueba de base y binarios |
| httpx simulado | Contrato del cliente de UI sin red |
| ruff | Lint estático (no es prueba, pero es gate del proyecto) |

## Modo TDD

`strict_tdd` está **desactivado** en la configuración del proyecto (repositorio documental sin runner al iniciar el ciclo). Las tareas de implementación están escritas en estilo RED+GREEN (primero la prueba, después el código); es una disciplina de ejecución del plan de tareas, no un gate del orquestador.

## Revisión de rendimiento (puerta de release)

| Elemento | Detalle |
| --- | --- |
| Siembra | ≥ 300 documentos y 100 usuarios (`scripts/seed_volume.py`) |
| Medición | Tiempos de listado, búsqueda y filtro anotados en el reporte de rendimiento del cambio |
| Índices | Toda columna filtrada debe estar indexada (NFR-02) |
| Ruta de mejora | Si la latencia no alcanza la meta (todavía por confirmar): FTS5 sobre metadatos |

## Qué no se automatiza en v1

- Pruebas de usabilidad de la UI Flet más allá del humo por objetivo (el diseño prueba el contrato del cliente, no píxeles).
- Pruebas de carga más allá del volumen sembrado confirmado.
- Pruebas de seguridad ofensiva más allá de los rechazos 401/403/404/413/415 y el endurecimiento de subida (matriz de amenazas: aplicable como no aplicable, salvo el manejo de la contraseña del CLI).

Los casos concretos derivados de las specs están en `01-test-cases.md`.
