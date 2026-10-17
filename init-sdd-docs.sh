#!/usr/bin/env bash
# =============================================================================
# init-sdd-docs.sh
#
# Genera la estructura canónica de documentación SDD (Spec-Driven Development)
# en CUALQUIER proyecto. Cada carpeta creada incluye un README.md que explica
# qué documentación se debe almacenar ahí.
#
# Uso:
#   ./init-sdd-docs.sh [directorio-destino]
#
#   Sin argumentos: crea la estructura en ./docs dentro del directorio actual.
#   Con argumento:  crea la estructura en <directorio-destino>/docs.
#   --dry-run:      muestra el árbol sin crear archivos.
#
# Ejemplos:
#   ./init-sdd-docs.sh                  # -> ./docs
#   ./init-sdd-docs.sh ~/mi-proyecto    # -> ~/mi-proyecto/docs
#   ./init-sdd-docs.sh --dry-run        # solo muestra el árbol
#
# El script es idempotente: no pisa archivos existentes.
# =============================================================================

set -euo pipefail

# -----------------------------------------------------------------------------
# Configuración
# -----------------------------------------------------------------------------

DRY_RUN=false
TARGET_DIR="."

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    -*)
      echo "Opción desconocida: $1" >&2
      echo "Uso: ./init-sdd-docs.sh [directorio-destino] [--dry-run]" >&2
      exit 1
      ;;
    *)
      TARGET_DIR="$1"
      shift
      ;;
  esac
done

DOCS_DIR="$TARGET_DIR/docs"

# -----------------------------------------------------------------------------
# Utilidades
# -----------------------------------------------------------------------------

# Escribe un archivo solo si no existe. Respeta el modo dry-run.
write_file() {
  local file="$1"
  local content="$2"

  if [[ "$DRY_RUN" == "true" ]]; then
    echo "  [crearía] $file"
    return
  fi

  if [[ -e "$file" ]]; then
    echo "  [ya existe] $file (no se pisa)"
    return
  fi

  mkdir -p "$(dirname "$file")"
  printf '%s\n' "$content" > "$file"
  echo "  [creado]   $file"
}

# Encabezado estándar para los README de cada carpeta.
carpeta_header() {
  local nombre="$1"
  local proposito="$2"
  cat <<EOF
# $nombre

$proposito

---
EOF
}

# -----------------------------------------------------------------------------
# README raíz
# -----------------------------------------------------------------------------

RAIZ_README='# Documentación del proyecto

La carpeta `docs` contiene toda la documentación funcional, conceptual y
técnica del proyecto. Es la **fuente de verdad**: antes de modificar código o
agregar funcionalidades, se debe revisar la documentación relacionada.

## Filosofía

Este proyecto usa **Specification Driven Development (SDD)**: primero se
comprende, luego se especifica, luego se diseña, luego se implementa y por
último se valida.

El orden recomendado es:

```
Comprender
    ↓
Especificar
    ↓
Diseñar
    ↓
Implementar
    ↓
Validar
```

La documentación debe evolucionar junto con el sistema. Si una funcionalidad
cambia una regla de negocio, primero se actualiza la especificación y después
el código.

## Estructura

```
docs/
├── README.md          → Esta guía
├── GLOSSARY.md        → Diccionario de términos SDD y del ecosistema
├── RESOURCES.md       → Recursos externos y guías de instalación
├── vision/            → Por qué existe el proyecto
├── requirements/      → Qué debe hacer el sistema
├── domain/            → Conceptos del negocio
├── architecture/      → Cómo se construye técnicamente
├── ui/                → Experiencia de usuario
├── use-cases/         → Interacciones entre actores y sistema
├── decisions/         → Decisiones de arquitectura (ADR)
├── specs/             → Especificaciones SDD por cambio
├── planning/          → Evolución del proyecto
├── reviews/           → Revisiones y auditorías
├── testing/           → Estrategia y casos de prueba
└── .ai/               → Contexto para agentes de IA
```

## Orden recomendado de lectura

Una persona nueva en el proyecto debería leer:

```
1. vision/README.md          → propósito y alcance
2. requirements/README.md    → reglas de negocio y funcionalidades
3. domain/README.md          → modelo conceptual
4. architecture/README.md    → decisiones técnicas
5. use-cases/README.md       → interacciones principales
```

## Regla principal

La documentación describe lo que el sistema **debe ser**, no lo que fue.
Mantenela sincronizada con el código: si el comportamiento cambia, primero
documentación, después implementación, después pruebas.
'

# -----------------------------------------------------------------------------
# GLOSSARY.md — diccionario de términos SDD
# -----------------------------------------------------------------------------

GLOSSARY_MD='# Glosario SDD: Specification-Driven Development

Diccionario de términos técnicos y conceptuales utilizados en el desarrollo de software guiado por especificaciones (**SDD**), orquestación de agentes con Inteligencia Artificial, control de contexto y el ecosistema web moderno.

---

## 1. Conceptos Centrales del Paradigma SDD

| Término | Definición Explicativa |
| :--- | :--- |
| **SDD** | *Spec-Driven Development (Desarrollo Guiado por Especificaciones).* Metodología de ingeniería de software donde el código no se escribe directamente, sino que se especifica primero. El ciclo sigue un orden estricto e inmutable: **Comprender $\rightarrow$ Especificar $\rightarrow$ Diseñar $\rightarrow$ Implementar $\rightarrow$ Validar**. Elimina la ambigüedad antes de la generación de código. |
| **OpenSpec** | Formato y estándar de arquitectura de archivos para proyectos basados en SDD. Define una estructura convencional dentro del repositorio, organizando las intenciones de cambio en `openspec/changes/` y las especificaciones consolidadas del sistema en `openspec/specs/`. |
| **Change** | La unidad fundamental de trabajo en SDD. Es un cambio nombrado, acotado y atómico sobre el sistema (ejemplo: `frontend-api-auth`). Agrupa de punta a punta todo el ciclo de vida del cambio: propuesta, especificación, diseño, desglose de tareas, aplicación y reporte de verificación. |
| **Delta Spec** | Especificación incremental escrita exclusivamente para describir las diferencias (el "delta") entre el estado actual del sistema y el estado deseado tras un `Change`. Al finalizar y aprobarse el cambio, este delta se consolida (*merge*) en la especificación principal del proyecto. |
| **Artifact Store** | El backend o repositorio de almacenamiento donde viven los artefactos generados en SDD. Puede configurarse como `openspec` (archivos Markdown directamente en el repositorio Git), `engram` (base de conocimientos/memoria persistente) o `hybrid` (sincronización entre ambos). |
| **Escenario** | Una situación concreta, observable y verificable que describe el comportamiento del sistema ante un estímulo o requisito. Sirve de puente entre el lenguaje de negocio y las pruebas automatizadas (ej: *"Dado un usuario no autenticado, cuando intenta ingresar a /admin, debe ser redirigido a /login"*). |
| **Criterio de Aceptación** | Condición objetiva y medible que un requisito, módulo o tarea debe cumplir obligatoriamente para ser considerado "Completado". Es la vara de medir del proceso de validación. |
| **Fortaleza de Requisito** | Nivel normativo de obligatoriedad dentro de una especificación, basado en la norma RFC 2119: **MUST** (obligación absoluta), **SHALL** (contrato estricto e inquebrantable), **SHOULD** (recomendación deseable, pero prescindible ante restricciones técnicas). |

---

## 2. Fases del Ciclo de Vida SDD

| Fase | Artefacto que produce | Pregunta fundamental que responde |
| :--- | :--- | :--- |
| **Explore** | `explore` | **¿Qué sabemos del problema?** Analiza el código existente, el contexto, la viabilidad y las dependencias afectadas antes de proponer soluciones. |
| **Propose** | `proposal` | **¿Qué cambio queremos hacer y por qué?** Define el alcance global, los objetivos, los no-objetivos, los riesgos y el impacto esperado. |
| **Spec** | `spec` | **¿Cuáles son los requisitos exactos?** Detalla la conducta requerida del sistema mediante requisitos y escenarios de prueba verificables (sin hablar de implementación). |
| **Design** | `design` | **¿Cómo lo construimos técnicamente?** Elige la arquitectura, estructuras de datos, endpoints, modelos de base de datos y patrones a utilizar. |
| **Tasks** | `tasks` | **¿En qué pasos se implementa?** Desglosa el diseño en una lista secuencial de tareas pequeñas, atómicas y ordenadas por dependencia. |
| **Apply** | `apply-progress` | **¿Se implementó el código?** Ejecuta la construcción del código tarea por tarea, registrando el avance y manteniendo la trazabilidad. |
| **Verify** | `verify-report` | **¿El código cumple la especificación?** Audita y ejecuta pruebas para validar que la implementación coincida exactamente con la spec original sin desviaciones. |
| **Archive** | `archive-report` | **¿Se cerró la unidad de trabajo?** Consolida la delta spec dentro de la documentación general del proyecto y archiva el registro del cambio. |

---

## 3. Artefactos y Persistencia

| Artefacto | Clave en Memoria (Topic Key) | Contenido y Propósito |
| :--- | :--- | :--- |
| **Proposal** | `sdd/{cambio}/proposal` | Documento inicial que argumenta la necesidad del cambio, delimita las fronteras del proyecto (alcance) y define qué cosas quedan explícitamente afuera (*no-objetivos*). |
| **Spec** | `sdd/{cambio}/spec` | Documento declarativo que contiene los requisitos funcionales, requisitos no funcionales y los escenarios de prueba en formato interpretable tanto por humanos como por IAs. |
| **Design** | `sdd/{cambio}/design` | Especificación técnica de ingeniería: patrones de software, modelos de datos, contratos de interfaz y diagramas de secuencia. |
| **Tasks** | `sdd/{cambio}/tasks` | Hoja de ruta de ejecución para el desarrollador o agente. Cada tarea debe ser lo suficientemente pequeña como para ser revisada y testeada de forma aislada. |
| **Apply Progress** | `sdd/{cambio}/apply-progress` | Bitácora de ejecución en tiempo real que documenta qué tareas fueron completadas, cuáles fallaron y qué archivos fueron modificados o creados. |
| **Verify Report** | `sdd/{cambio}/verify-report` | Informe de auditoría técnica que certifica el porcentaje de cumplimiento de la especificación y lista cualquier inconsistencia o regresión detectada. |
| **Archive Report** | `sdd/{cambio}/archive-report` | Registro de cierre definitivo. Certifica la incorporación de la nueva funcionalidad a la rama principal de código (*main*) y consolida los cambios en el cuerpo de specs. |

---

## 4. Roles, Agentes y Control de Ejecución

| Término | Definición Explicativa |
| :--- | :--- |
| **Orchestrator** | El agente inteligente principal que coordina el flujo global. Delega tareas específicas a sub-agentes especializados, valida los artefactos producidos, sintetiza los resultados y mantiene el hilo de conversación limpio y dentro de presupuesto. |
| **Sub-agente** | Un agente con un propósito único y acotado (ej: *Sub-agente de Pruebas*, *Sub-agente de Revisión de Seguridad*). Se instancia con un contexto fresco y limitado para ejecutar su tarea rápida y eficientemente. |
| **Skill** | Archivo de instrucción especializada (`SKILL.md`) que le enseña a un agente una competencia procedimental específica: escribir tests con TDD, realizar reviews de código, gestionar PRs o crear esquemas de base de datos. |
| **Prompt Estructurado** | Instrucción parametrizada y determinista diseñada para una fase concreta de SDD. A diferencia del prompting informal, exige formatos de respuesta rígidos para evitar alucinaciones. |
| **Persona** | Configuración de tono, estilo de comunicación y lenguaje que utiliza la IA al dirigirse al usuario. Define la experiencia conversacional sin interferir en los contratos técnicos de los artefactos Markdown. |
| **Gatekeeper** | Mecanismo de validación e inspección que ejecuta el orquestador al finalizar cada fase. Verifica que el artefacto sea válido, que no contenga alucinaciones y que cumpla los criterios antes de habilitar el paso a la siguiente fase. |

---

## 5. Gestión de Contexto, Prompts y Seguridad de IA

| Término | Definición Explicativa |
| :--- | :--- |
| **Context Window** | Tamaño máximo de memoria de trabajo (medido en *tokens*) que el modelo de lenguaje puede procesar en una sola interacción. Gestionar la ventana de contexto evita la "amnesia" del modelo y reduce costos de API. |
| **Token Budget** | Límite máximo de procesamiento asignado a una fase o sub-agente. Evita que un bucle infinito de refactorización consuma recursos innecesarios. |
| **System Prompt** | La directiva base inmutable que establece la "personalidad", las capacidades, el rol y los límites de seguridad de la IA antes de que el usuario envíe su primer mensaje. |
| **Grounding** | Técnica de anclaje que obliga a la IA a basar sus respuestas únicamente en documentación verídica y especificaciones inmutables provistas (como las carpetas `specs/`), impidiendo que invente funcionalidades. |
| **Few-Shot Prompting** | Estructuración de instrucciones que incluye ejemplos concretos de entrada y salida esperada dentro de la especificación, garantizando que el código generado replique exactamente las convenciones del proyecto. |
| **Prompt Injection** | Vulnerabilidad de seguridad donde datos externos o manipulados insertados en la entrada del sistema logran alterar las instrucciones originales del `System Prompt` del agente. |
| **Agentic Loop** | El ciclo autónomo de interacción de un agente: **Observar la herramienta/sistema $\rightarrow$ Analizar el resultado $\rightarrow$ Decidir la siguiente acción $\rightarrow$ Ejecutar comando**. |
| **Tool Calling / Function Calling** | Habilidad técnica de los modelos de IA de interpretar una necesidad y solicitar la ejecución de una herramienta del sistema (ej: leer un archivo local, correr un script de prueba o consultar la base de datos). |

---

## 6. Flujo de Trabajo, Sesiones y Entrega

| Término | Definición Explicativa |
| :--- | :--- |
| **Session Preflight** | Protocolo obligatorio de inicialización al comenzar una sesión de trabajo en SDD. Configura el modo de ejecución, el almacén de artefactos, la estrategia de entrega e inspecciona la memoria. |
| **Modo de Ejecución** | El ritmo de automatización de la sesión: **Interactive** (pausa el flujo tras cada fase para requerir aprobación humana) o **Auto** (cadena la ejecución continua respaldada por la supervisión de los *gatekeepers*). |
| **Review Workload Guard** | Freno automático de seguridad antes de la fase de implementación (`apply`). Si el plan de tareas pronostica una modificación superior a 400 líneas de código o implica áreas de alto riesgo, exige aprobación explícita. |
| **Delivery Strategy** | Estrategia de integración continua para Pull Requests. Define reglas como `ask-on-risk` (consultar ante cambios críticos), `auto-chain` (crear PRs acumulativos), `single-pr` (unificar todo el cambio en un solo PR) o `exception-ok`. |
| **Chain Strategy** | Estrategia de bifurcación en Git para cambios complejos: `stacked-to-main` (PRs dependientes alineados a la rama principal) o `feature-branch-chain` (PRs secundarios sobre una rama acumuladora de funcionalidad). |
| **size:exception** | Etiqueta o autorización formal otorgada por el mantenedor del proyecto que permite omitir la restricción máxima de 400 líneas de código para un PR de naturaleza masiva (ej: migraciones de datos). |

---

## 7. Ecosistema de Herramientas y Entorno Local

| Término | Definición Explicativa |
| :--- | :--- |
| **opencode** | Entorno de desarrollo de línea de comandos (CLI) optimizado para programación asistida y orquestación de agentes con Inteligencia Artificial. |
| **gentle-ai** | Framework de extensión para `opencode` que implementa nativamente la metodología SDD, integrando soporte para memoria, habilidades (`skills`) y auditoría de código. |
| **Engram** | Sistema de base de datos de memoria persistente a largo plazo. Permite a los agentes recordar decisiones de arquitectura, bugs históricos y patrones de código a través de diferentes sesiones de trabajo. |
| **AGENTS.md** | Archivo de configuración ubicado en la raíz del proyecto que dicta las instrucciones de comportamiento, restricciones y estándares que todos los agentes deben obedecer dentro de ese repositorio. |
| **ADR** | *Architecture Decision Record (Registro de Decisión de Arquitectura).* Documento breve que captura una decisión clave de infraestructura o diseño tomada en el proyecto, documentando su contexto, alternativas y consecuencias. |
| **MCP** | *Model Context Protocol (Protocolo de Contexto de Modelo).* Estándar abierto para la comunicación de contexto que permite conectar IAs con herramientas locales, bases de datos y APIs externas de forma segura. |
| **Topic Key** | Cadena identificadora única (ej: `sdd/{cambio}/tasks`) que indexa datos dentro de la memoria `Engram`. Permite consultar, actualizar o sobreescribir información sobre un tema sin duplicar registros. |
| **Operaciones mem_\*** | Conjunto de funciones de la interfaz de `Engram`: `mem_save` (guardar memoria), `mem_search` (buscar por coincidencia vectorial/semántica), `mem_context` (recuperar el contexto reciente) y `mem_session_summary` (generar un resumen al cerrar la sesión). |

---

## 8. Calidad, Testing y Entrega Continua

| Término | Definición Explicativa |
| :--- | :--- |
| **Definition of Done (DoD)** | Lista formal de comprobación técnica que determina si una tarea está lista para producción (código limpio, especificación cumplida, tests aprobados y documentación actualizada). |
| **Work Unit Commit** | Estrategia de versión en Git donde cada *commit* constituye una unidad atómica y funcional que incluye el código de la característica, su prueba automatizada y la especificación asociada. |
| **Chained PR** | División de un cambio grande en múltiples Pull Requests encadenados y pequeños (de menos de 400 líneas cada uno) para acelerar y simplificar la revisión humana. |
| **Review** | Fase de evaluación estricta donde el código producido por el agente se examina bajo distintas perspectivas antes de integrarse al repositorio. |
| **Lentes de Review** | Enfoques analíticos aplicados durante la auditoría de código: **R1 (Riesgo)**, **R2 (Legibilidad y estilo)**, **R3 (Confiabilidad y corrección)** y **R4 (Resiliencia y manejo de errores)**. |
| **TDD / Strict TDD** | *Test-Driven Development (Desarrollo Guiado por Pruebas).* Práctica donde la prueba automatizada se escribe obligatoriamente antes que el código de producción. En el modo *Strict TDD*, el agente tiene prohibido generar lógica si no existe un test fallando previamente. |
| **Candidate** | La versión o "foto" inmutable del código propuesto que se envía al proceso de auditoría y pruebas. |
| **Base Inmutable** | Punto de congelamiento del árbol de archivos contra el cual se compara el `Candidate` durante la revisión para asegurar que no se introdujeron cambios no autorizados. |
| **Receipt** | Certificado criptográfico o registro emitido por el sistema de verificación que garantiza que un cambio fue auditado y aprobado exitosamente, habilitando las operaciones de *push* o *merge*. |
| **Judgment Day** | Proceso de revisión crítico y de alta seguridad para cambios sensibles (ej: infraestructura financiera o autenticación). Emplea dos agentes evaluadores independientes actuando de forma ciega y adversarial. |

---

## 9. Arquitectura y Desarrollo Web

| Término | Definición Explicativa |
| :--- | :--- |
| **SSR** | *Server-Side Rendering (Renderizado en Servidor).* Técnica donde el servidor procesa el código y genera la página HTML completa antes de enviarla al cliente. Optimiza el tiempo de carga inicial y favorece el posicionamiento en buscadores (SEO). |
| **CSR** | *Client-Side Rendering (Renderizado en Cliente).* El servidor envía una estructura HTML mínima y el navegador ejecuta código JavaScript para descargar datos y construir la interfaz dinámicamente. |
| **Hydration (Hidratación)** | Proceso mediante el cual el navegador toma el HTML estático enviado por el servidor (SSR) y le adjunta los escuchadores de eventos y el estado de JavaScript, haciendo la interfaz plenamente interactiva. |
| **SPA** | *Single Page Application (Aplicación de Página Única).* Aplicación web que carga un solo documento HTML y actualiza dinámicamente secciones de la pantalla mediante llamadas a APIs sin recargar el navegador. |
| **Framework vs Librería** | Una librería es un conjunto de herramientas que el desarrollador invoca a voluntad. Un framework (ej: SvelteKit, FastAPI) impone la arquitectura del sistema y toma el control del flujo de ejecución (*Inversión de Control*). |
| **Componente** | Módulo de código reutilizable e independiente que encapsula la lógica, la estructura (HTML) y la presentación (CSS) de una pieza de la interfaz de usuario. |
| **Bundler** | Herramienta de compilación (ej: Vite) que empaqueta, optimiza y transforma los módulos y recursos del proyecto en archivos estáticos eficientes para el navegador. |
| **API / Endpoint** | La API es el contrato global de comunicación entre sistemas. Un *Endpoint* es la ruta o URL concreta (ej: `POST /api/v1/auth/login`) expuesta para realizar una operación específica. |
| **REST / CRUD** | *REST* es el estilo arquitectónico de comunicación basado en recursos HTTP. *CRUD* representa las cuatro operaciones fundamentales sobre cualquier entidad de datos: Create (Crear), Read (Leer), Update (Actualizar) y Delete (Eliminar). |
| **Middleware** | Función o capa intermedia que intercepta una solicitud HTTP antes de que alcance el controlador final. Se utiliza para tareas transversales como validación de tokens de sesión, logging o CORS. |
| **ORM / Migración** | El *ORM* (Object-Relational Mapping) traduce entidades del lenguaje de programación a tablas de una base de datos relacional. Una *Migración* es un script versionado que altera de forma controlada el esquema de la base de datos. |
| **JWT** | *JSON Web Token.* Estándar de autenticación compacto y autosuficiente que transporta información del usuario encriptada o firmada digitalmente entre el cliente y el servidor. |
| **Svelte / SvelteKit** | *Svelte* es un compilador web que transforma el código en JavaScript imperativo ultra-optimizado durante la fase de *build*, sin utilizar un Virtual DOM. *SvelteKit* es su framework oficial para aplicaciones SSR/CSR. |
| **FastAPI** | Framework de Python de alto rendimiento diseñado para construir APIs REST asíncronas, con tipado estricto y generación automática de documentación interactiva (OpenAPI/Swagger). |
| **Contenedor / Podman / Docker** | Tecnología de virtualización a nivel de sistema operativo que empaqueta una aplicación y todo su entorno de ejecución dentro de una unidad aislada e independiente de la máquina anfitriona. |

---

## 10. Documentación de Proyecto e Invariantología

| Término | Definición Explicativa |
| :--- | :--- |
| **Visión** | Declaración estratégica de alto nivel que define el propósito supremo del proyecto, el problema que busca resolver y sus métricas de éxito a largo plazo. |
| **Requisito Funcional** | Declaración de una capacidad o comportamiento explícito que el sistema **debe realizar** (ej: *"El sistema debe permitir filtrar productos por rango de precio"*). |
| **Requisito No Funcional** | Restricción cualitativa o técnica sobre cómo debe operar el sistema (ej: *"La latencia de la API no debe superar los 200 ms bajo una carga de 1000 usuarios concurrentes"*). |
| **Regla de Negocio** | Política, restricción o condición inquebrantable del dominio de aplicación que gobierna la lógica del sistema (ej: *"Un cupón de descuento no puede aplicarse a productos que ya están en oferta"*). |
| **Modelo de Dominio** | Representación conceptual de los objetos reales o abstractos del negocio, sus atributos y la forma en que se relacionan entre sí dentro de la aplicación. |
| **User Story** | Especificación breve de una necesidad desde la perspectiva del usuario final, expresada habitualmente en la estructura: *"Como [rol], quiero [acción] para [beneficio]"*. |
| **No-Objetivo (Out of Scope)** | Declaración explícita e implacable de las cosas que el proyecto o el cambio **NO va a construir**. Es el escudo principal para prevenir la expansión descontrolada del alcance (*scope creep*). |
'

# -----------------------------------------------------------------------------
# RESOURCES.md — recursos externos y guías de instalación
# -----------------------------------------------------------------------------

RESOURCES_MD='# Recursos externos

Guías y referencias para instalar el entorno de desarrollo basado en IA que
acompaña a este proyecto.

## 1. Instalar opencode

opencode es la terminal de programación con IA donde corre todo el flujo SDD.

**Requisito previo:** Node.js 20+ (recomendado: v22 LTS o superior).

Instalación global vía npm:

```bash
npm install -g opencode-ai
```

Verificá la instalación:

```bash
opencode --version
```

Al primer arranque, opencode te pedirá elegir el modelo de IA que quieras usar.

## 2. Instalar el ecosistema Gentleman Programming (gentle-ai)

El framework **gentle-ai** agrega SDD, skills, reviews y memoria persistente al
entorno. Instalalo siguiendo la guía oficial del perfil **@gentlemanprogramming**.

Una vez instalado el binario, los comandos principales son:

```bash
# Configura los agentes de IA en la máquina (skills, AGENTS.md, permisos)
gentle-ai install

# Sincroniza configs y skills a la versión actual
gentle-ai sync

# Refresca el índice de skills con ruta de caché rápida
gentle-ai skill-registry refresh
```

Verificá la instalación:

```bash
gentle-ai --help
```

## 3. Habilitar la memoria persistente (Engram)

Engram guarda decisiones, bugs y artefactos SDD entre sesiones. Se conecta como
servidor MCP dentro de opencode.

- **`mem_save`**: guarda una observación (decisión, bug, patrón).
- **`mem_search`**: busca observaciones previas por palabras clave.
- **`mem_context`**: recupera el contexto de sesiones recientes.
- **`mem_session_summary`**: guarda el resumen de cierre de sesión.

## 4. Estructura de configuración del entorno

| Ruta | Qué contiene |
| ---- | ------------ |
| `~/.config/opencode/` | Configuración global de opencode: agentes, skills, permisos. |
| `~/.config/opencode/AGENTS.md` | Reglas de persona y protocolos para los agentes. |
| `~/.config/opencode/skills/` | Skills instalados (`sdd-*`, review, chained-pr, etc.). |
| `.atl/skill-registry.md` | Índice de skills del proyecto (se regenera con `gentle-ai skill-registry refresh`). |
| `openspec/` | Artefactos SDD del proyecto (cambios y specs consolidadas). |

## 5. Referencias de conceptos

- **Spec-Driven Development (SDD):** la metodología de este proyecto. Ver `GLOSSARY.md`.
- **Architecture Decision Records (ADR):** ver `docs/decisions/README.md`.
- **Definition of Done:** ver `docs/.ai/definition-of-done.md` si el proyecto la define.
'

# -----------------------------------------------------------------------------
# Contenido de cada carpeta
# -----------------------------------------------------------------------------

# 1. Vision
VISION_README="$(carpeta_header "Vision" \
"Define la razón de existir del proyecto: qué problema resuelve, quién lo
usará, cuáles son los objetivos y cuál es el alcance inicial.")"

# 2. Requirements
REQUIREMENTS_README="$(carpeta_header "Requirements" \
"Define qué debe hacer el sistema: reglas de negocio, funcionalidades,
restricciones y comportamientos esperados.")"""

# 3. Domain
DOMAIN_README="$(carpeta_header "Domain" \
"Define los conceptos principales del negocio: entidades, relaciones y la
información que representa cada una.")"""

# 4. Architecture
ARCHITECTURE_README="$(carpeta_header "Architecture" \
"Define cómo se construye técnicamente el sistema: tecnologías, componentes,
comunicación entre servicios, seguridad y despliegue.")"""

# 5. UI
UI_README="$(carpeta_header "UI" \
"Define la experiencia de usuario: pantallas, navegación, componentes y
sistema visual.")"""

# 6. Use Cases
USECASES_README="$(carpeta_header "Use Cases" \
"Define las interacciones entre los actores y el sistema para lograr un
objetivo concreto.")"""

# 7. Decisions
DECISIONS_README="$(carpeta_header "Decisions" \
"Registro de Decisiones de Arquitectura (ADR): decisiones importantes, su
contexto, la alternativa elegida y el motivo.")"""

# 8. Specs
SPECS_README="$(carpeta_header "Specs" \
"Especificaciones SDD. Cada cambio del proyecto tiene su propia
especificación (delta spec) con requisitos y escenarios.")"""

# 9. Planning
PLANNING_README="$(carpeta_header "Planning" \
"Define la evolución del proyecto: roadmap, hitos, preguntas abiertas y
registro de cambios.")"""

# 10. Reviews
REVIEWS_README="$(carpeta_header "Reviews" \
"Revisiones y auditorías realizadas sobre el proyecto: hallazgos, decisiones
tomadas y seguimiento.")"""

# 11. Testing
TESTING_README="$(carpeta_header "Testing" \
"Estrategia de pruebas y casos de prueba del proyecto.")"""

# 12. .ai (contexto para agentes)
AI_README="$(carpeta_header ".ai (contexto para agentes de IA)" \
"Contexto que los agentes de IA leen antes de trabajar: contexto del
proyecto, guía de prompts, workflow, estándares y definition of done.")"

# -----------------------------------------------------------------------------
# Detalle de cada carpeta: archivos esperados
# -----------------------------------------------------------------------------

VISION_README+="
## Documentos esperados

| Archivo | Qué contiene |
| ------- | ------------ |
| \`vision.md\` | Visión general del proyecto: problema que resuelve, usuarios. |
| \`glossary.md\` | Definición de términos importantes del dominio. |
| \`objectives.md\` | Objetivos del sistema, medibles si es posible. |
| \`scope.md\` | Alcance y límites: qué se incluye y qué no. |

## Consejos

- Empezá por \`vision.md\`: si no podés explicar el problema en una página,
  todavía no estás listo para codear.
- El alcance es dinámico: actualizalo cuando el proyecto crezca o cambie.
"

REQUIREMENTS_README+="
## Documentos esperados

| Archivo | Qué contiene |
| ------- | ------------ |
| \`business-rules.md\` | Reglas que gobiernan el comportamiento del sistema. |
| \`functional-requirements.md\` | Funcionalidades que debe ofrecer la aplicación. |
| \`non-functional-requirements.md\` | Calidad, rendimiento, seguridad, restricciones. |
| \`authentication.md\` | Especificación de autenticación y autorización. |
| \`user-stories.md\` | Necesidades expresadas desde la perspectiva del usuario. |

## Consejos

- Las reglas de negocio son la fuente de verdad para los casos de prueba.
- Cada requisito funcional debería poder rastrearse hasta su implementación.
"

DOMAIN_README+="
## Documentos esperados

| Archivo | Qué contiene |
| ------- | ------------ |
| \`domain-model.md\` | Modelo conceptual del sistema: conceptos y relaciones. |
| \`entities.md\` | Descripción detallada de cada entidad y sus atributos. |
| \`data-model.md\` | Esquema físico: tablas, columnas, índices y relaciones. |

## Consejos

- El modelo de dominio debe entenderse sin leer código.
- Cuando cambia una entidad, actualizá el dominio ANTES del schema.
"

ARCHITECTURE_README+="
## Documentos esperados

| Archivo | Qué contiene |
| ------- | ------------ |
| \`00-architecture.md\` | Arquitectura general: componentes y comunicación. |
| \`01-api-design.md\` | Diseño de APIs y contratos entre servicios. |
| \`02-security.md\` | Modelo de seguridad: autenticación, autorización, datos. |
| \`03-deployment.md\` | Estrategia de despliegue: ambientes, contenedores, CI/CD. |
| \`04-decisions.md\` | Índice de decisiones técnicas del proyecto. |

## Consejos

- Los diagramas ayudan, pero deben tener texto que los explique.
- Las decisiones técnicas grandes van en \`docs/decisions/\` como ADR.
"

UI_README+="
## Documentos esperados

| Archivo | Qué contiene |
| ------- | ------------ |
| \`00-ui-overview.md\` | Visión general de la interfaz, temas y modos. |
| \`01-pages.md\` | Definición de pantallas, navegación y estados vacíos. |
| \`02-components.md\` | Componentes reutilizables de la UI. |
| \`03-design-system.md\` | Reglas visuales: paleta, tipografía, espaciado, dark mode. |

## Consejos

- Documentá los estados vacíos y de error: son los que más se olvidan.
- Si cambiás un componente, actualizá su documentación en el mismo cambio.
"

USECASES_README+="
## Documentos esperados

Un archivo por caso de uso o grupo de casos relacionados, con el actor, la
precondición, el flujo principal y los flujos alternativos:

| Archivo | Qué contiene |
| ------- | ------------ |
| \`<caso-de-uso>.md\` | Un caso de uso o grupo relacionado (ej: \`users.md\`, \`recipes.md\`). |
| \`README.md\` | Este índice: lista los casos de uso y su estado. |

## Consejos

- Un caso de uso debe ser accionable: el lector entiende qué hace el sistema.
- Los casos de uso alimentan los casos de prueba de \`docs/testing/\`.
"

DECISIONS_README+="
## Formato ADR

Cada decisión de arquitectura importante se registra como ADR numerado:

\`\`\`
ADR-XXX-nombre-breve.md
\`\`\`

Contenido mínimo:

| Sección | Qué contiene |
| ------- | ------------ |
| Título | Número y nombre de la decisión. |
| Contexto | Problema o situación que motivó la decisión. |
| Decisión | Qué se decidió, concreto y sin ambigüedad. |
| Alternativas | Qué se descartó y por qué. |
| Consecuencias | Impacto positivo y negativo de la decisión. |

## Consejos

- Un ADR se escribe cuando se TOMA la decisión, no después.
- Los ADR son inmutables: si la decisión cambia, se crea un ADR nuevo.
"

SPECS_README+="
## Estructura SDD

Cada cambio del proyecto sigue el ciclo SDD:

\`\`\`
proposal → spec → design → tasks → apply → verify → archive
\`\`\`

En esta carpeta se guardan las especificaciones (delta specs) con formato:

\`\`\`
specs/<nombre-del-cambio>.md
\`\`\`

Cada spec contiene requisitos con su fortaleza (MUST / SHALL / SHOULD) y
escenarios verificables.

## Documentos esperados

| Archivo | Qué contiene |
| ------- | ------------ |
| \`README.md\` | Este índice y guía del ciclo SDD. |
| \`TEMPLATE.md\` | Plantilla para escribir una spec nueva. |
| \`<cambio>.md\` | Spec de un cambio concreto (se agrega con cada change). |

## Consejos

- La spec se escribe ANTES del código: es el contrato del cambio.
- Si un requisito no se puede verificar, no es un requisito.
"

PLANNING_README+="
## Documentos esperados

| Archivo | Qué contiene |
| ------- | ------------ |
| \`00-roadmap.md\` | Evolución planificada del proyecto. |
| \`01-milestones.md\` | Hitos principales con objetivos verificables. |
| \`02-open-questions.md\` | Preguntas sin resolver y decisiones pendientes. |
| \`03-changelog.md\` | Historial de cambios por versión. |

## Consejos

- El roadmap es una hipótesis: se revisa en cada milestone.
- Las preguntas abiertas bloquean diseño: resolvelas temprano.
"

REVIEWS_README+="
## Documentos esperados

| Archivo | Qué contiene |
| ------- | ------------ |
| \`<fecha>-<tema>.md\` | Revisión o auditoría con hallazgos y acciones. |

## Consejos

- Una revisión sin fecha y sin acciones no sirve: registrá ambas.
- El seguimiento de hallazgos se hace acá o en \`docs/planning/\`.
"

TESTING_README+="
## Documentos esperados

| Archivo | Qué contiene |
| ------- | ------------ |
| \`00-strategy.md\` | Estrategia de pruebas: niveles, herramientas, cobertura. |
| \`01-test-cases.md\` | Casos de prueba derivados de reglas de negocio y casos de uso. |

## Consejos

- Cada regla de negocio de \`docs/requirements/\` debería tener su caso de prueba.
- En SDD, los tests se escriben contra la spec, no contra la implementación.
"

AI_README+="
## Documentos esperados

| Archivo | Qué contiene |
| ------- | ------------ |
| \`project-context.md\` | Contexto del proyecto para que un agente nuevo arranque rápido. |
| \`prompt-guide.md\` | Cómo escribir prompts efectivos para este proyecto. |
| \`workflow.md\` | Flujo de trabajo: cómo se hacen los cambios, reviews y commits. |
| \`glossary.md\` | Glosario del proyecto (además del glosario SDD global). |
| \`definition-of-done.md\` | Criterios de terminado para tareas y cambios. |
| \`coding-standards.md\` | Estándares de código del proyecto. |

## Consejos

- Este contexto es lo primero que lee un agente de IA antes de trabajar.
- Mantenelo corto y accionable: los agentes no leen manuales largos.
"

# -----------------------------------------------------------------------------
# Generación
# -----------------------------------------------------------------------------

echo "=== init-sdd-docs.sh ==="
echo "Destino: $DOCS_DIR"
echo ""

if [[ "$DRY_RUN" == "true" ]]; then
  echo "Modo dry-run: no se crea ningún archivo."
  echo ""
fi

write_file "$DOCS_DIR/README.md"       "$RAIZ_README"
write_file "$DOCS_DIR/GLOSSARY.md"     "$GLOSSARY_MD"
write_file "$DOCS_DIR/RESOURCES.md"    "$RESOURCES_MD"

write_file "$DOCS_DIR/vision/README.md"       "$VISION_README"
write_file "$DOCS_DIR/requirements/README.md" "$REQUIREMENTS_README"
write_file "$DOCS_DIR/domain/README.md"       "$DOMAIN_README"
write_file "$DOCS_DIR/architecture/README.md" "$ARCHITECTURE_README"
write_file "$DOCS_DIR/ui/README.md"           "$UI_README"
write_file "$DOCS_DIR/use-cases/README.md"    "$USECASES_README"
write_file "$DOCS_DIR/decisions/README.md"    "$DECISIONS_README"
write_file "$DOCS_DIR/specs/README.md"        "$SPECS_README"
write_file "$DOCS_DIR/planning/README.md"     "$PLANNING_README"
write_file "$DOCS_DIR/reviews/README.md"      "$REVIEWS_README"
write_file "$DOCS_DIR/testing/README.md"      "$TESTING_README"
write_file "$DOCS_DIR/.ai/README.md"          "$AI_README"

echo ""
echo "=== Estructura generada ==="

# Lista explícita de archivos (también sirve para el dry-run sin tocar disco).
ARCHIVOS=(
  "README.md"
  "GLOSSARY.md"
  "RESOURCES.md"
  "vision/README.md"
  "requirements/README.md"
  "domain/README.md"
  "architecture/README.md"
  "ui/README.md"
  "use-cases/README.md"
  "decisions/README.md"
  "specs/README.md"
  "planning/README.md"
  "reviews/README.md"
  "testing/README.md"
  ".ai/README.md"
)

for archivo in "${ARCHIVOS[@]}"; do
  echo "  $DOCS_DIR/$archivo"
done

echo ""
if [[ "$DRY_RUN" == "true" ]]; then
  echo "Modo dry-run: nada fue creado. Corré sin --dry-run para generar la estructura."
else
  echo "Listo. La documentación de tu proyecto queda en: $DOCS_DIR"
  echo "Empezá por docs/README.md"
fi
