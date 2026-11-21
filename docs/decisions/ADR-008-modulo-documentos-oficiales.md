# ADR-008: Módulo `app/documentos_oficiales/` con entry points en `app/`

## Contexto

El código funcional del sistema (ajustes, base de datos, servicios, API y UI Flet) vivía repartido en `app/core/`, `app/db/`, `app/services/`, `app/api/` y `app/ui/`, mezclado con los tres entry points (`app/main.py`, `app/server.py`, `app/cli.py`). Al evaluar cómo crecer la estructura se planteó extraer todo a un sistema nuevo —nombre y repositorio aparte— para darle identidad propia. Con un solo módulo funcional, esa extracción no aporta ningún beneficio estructural que justifique el costo de un repo/nombre nuevos; además la extracción sigue siendo barata después, si aparece un segundo sistema real.

## Decisión

El sistema app-docs organiza su código funcional en el subpaquete `app/documentos_oficiales/` (`core/`, `db/`, `services/`, `api/`, `ui/`), y los entry points permanecen en la raíz de `app/`: `uvicorn app.main:app`, `uvicorn app.server:app` y `python -m app.cli create-admin` no cambian. Los imports hacia el código funcional apuntan al subpaquete; los imports entre entry points (`app.server` → `app.main`) no.

## Alternativas

| Alternativa | Motivo de descarte |
| --- | --- |
| Extraer todo a un repo/nombre de sistema nuevo | Con un solo módulo no hay beneficio estructural que justifique el costo (repo, release, versionado independientes); la extracción sigue siendo barata más adelante si aparece un segundo sistema. |
| Dejar el código funcional mezclado en la raíz de `app/` | Los entry points y el código quedan indistinguibles; cada archivo nuevo obliga a decidir a mano si es entry point o dominio, y la frontera se degrada con el tiempo. |

## Consecuencias

- **Positivas**: una frontera explícita entre lo que se invoca (`app/main.py`, `app/server.py`, `app/cli.py`) y lo que se compone (`app/documentos_oficiales/**`); los entry points quedan estables aunque el interior se reorganice; mover un directorio completo es un solo `mv` + reescritura de imports.
- **Negativas / riesgos**: una capa más de profundidad en rutas y en `parents[N]` al resolver la raíz del proyecto desde `app/documentos_oficiales/ui/main.py`; los comandos de desarrollo (`flet run …`, `pkill -f …`) y la documentación de paths deben mencionar la ruta larga.
- **Regla**: no extraer un `core/` compartido hasta que un segundo módulo lo requiera — con n=1 no se deciden fronteras.

Ver `../architecture/04-decisions.md` (índice) y `../architecture/00-architecture.md` (componentes).
