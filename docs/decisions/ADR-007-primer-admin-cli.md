# ADR-007: Bootstrap del primer administrador por comando de terminal

## Contexto

El sistema prohíbe el auto-registro: no existen rutas de registro propio. En una instalación fresca, tras `create_all` no hay ninguna cuenta, y la interfaz exige una sesión para funcionar — el clásico huevo-y-gallina: sin administrador no hay alta de cuentas, y sin sesión no hay interfaz de administración. Además, la creación no puede pasar por credenciales en variables de entorno de un proceso de larga duración.

## Decisión

El primer administrador se crea con un **comando explícito de terminal**, al estilo del `createsuperuser` de Django:

```
python -m app.cli create-admin                     # pide usuario y contraseña (getpass, sin eco)
python -m app.cli create-admin --username <nombre> # la contraseña siempre se pide; jamás por argv
```

El comando se niega a ejecutarse si `users` ya contiene un administrador, salvo que se pase `--force`. Hashea la contraseña con el mismo camino `core/security.py` (bcrypt) que se usa en runtime y escribe una fila en `users`. `app/cli.py` usa `argparse` y `getpass` de la biblioteca estándar — sin dependencias nuevas. Esta es la **única** forma en que una cuenta de administrador llega a existir en una instalación nueva. Si no hay administradores, la API devuelve 401 y la interfaz muestra un mensaje en español que indica al operador que ejecute el comando.

## Alternativas

| Alternativa | Motivo de descarte |
| --- | --- |
| Variables de entorno `DOCMANAGER_BOOTSTRAP_ADMIN_*` leídas al arrancar | El secreto queda en el entorno del proceso de larga duración, visible para quien inspeccione el proceso o su unidad systemd, y se re-ejecuta silenciosamente en cada reinicio. |
| Fixture de semilla con contraseña en el repositorio | Contraseña compartida en control de versiones. |
| Crear el primer usuario desde la UI Flet antes de existir auth | La UI exige una sesión, que es exactamente el huevo-y-gallina. |

## Consecuencias

- **Positivas**: sigue la instrucción explícita del usuario y el patrón probado de Django; la credencial la teclea una persona en una terminal de operador y nunca se persiste fuera de la fila hasheada de `users`; funciona igual en despliegues web, escritorio y móvil porque solo toca la base de datos, no la superficie HTTP; la contraseña no cae en historial del shell, `ps` ni logs (NFR-07).
- **Negativas / riesgos**: un paso operativo extra tras `create_all` en la instalación fresca; el mensaje en español de la UI ante cero administradores es parte del contrato (debe quedar claro que no es un fallo del sistema).

Ver `../requirements/authentication.md` y el caso de uso `../use-cases/inicio-sesion-y-roles.md` (nota de arranque).
