# Documentación del proyecto

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

