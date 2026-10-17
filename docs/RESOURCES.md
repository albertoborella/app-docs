# Recursos externos

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

