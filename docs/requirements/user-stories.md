# Historias de usuario

Necesidades expresadas desde la perspectiva de cada actor, derivadas exclusivamente de requisitos y decisiones `CONFIRMADO` del cambio `dairy-doc-manager`. No se inventan prioridades ni estimaciones: la columna de estado refleja el alcance confirmado del primer slice.

## Administrador del sistema

| ID | Historia | Estado | Fuente |
| --- | --- | --- | --- |
| US-01 | Como administrador, quiero crear un documento con sus campos y guardar el registro en el catálogo, para mantener la documentación oficial al día. | En alcance | spec `document-management` |
| US-02 | Como administrador, quiero modificar cualquier campo de un documento existente, para corregir o actualizar información sin duplicar registros. | En alcance | spec `document-management` |
| US-03 | Como administrador, quiero retirar un documento obsoleto (borrado suave) y restaurarlo si hace falta, para que salga del catálogo sin perder el registro ni el archivo. | En alcance | spec `document-management`, ADR-005 |
| US-04 | Como administrador, quiero subir el archivo de un documento (PDF u otro formato permitido) y reemplazarlo, para que los usuarios descarguen el binario correcto. | En alcance | spec `document-file-storage` |
| US-05 | Como administrador, quiero ver la papelera de documentos retirados, para auditar qué se quitó del catálogo y recuperarlo. | En alcance | spec `document-management` |
| US-06 | Como administrador, quiero crear cuentas de usuario asignando el rol (administrador o normal), para dar acceso al personal autorizado. | En alcance | spec `user-account-management` |
| US-07 | Como administrador, quiero editar una cuenta y desactivarla o reactivarla, para retirar el acceso de una persona sin borrar su registro. | En alcance | spec `user-account-management` |
| US-08 | Como administrador, quiero editar la contraseña de una cuenta desde la interfaz de administración, para gestionar credenciales sin un flujo de autoservicio. | En alcance | diseño (rutas de usuarios) |

## Usuario normal

| ID | Historia | Estado | Fuente |
| --- | --- | --- | --- |
| US-09 | Como usuario, quiero iniciar sesión con mi usuario y contraseña provistos por el administrador, para acceder al catálogo. | En alcance | spec `user-account-management` |
| US-10 | Como usuario, quiero ver el catálogo completo de documentos oficiales, para consultar la documentación vigente de la empresa. | En alcance | spec `document-management` |
| US-11 | Como usuario, quiero buscar en el catálogo y filtrar la lista, para localizar rápidamente la documentación que necesito. | En alcance (dimensiones exactas de filtro: `CONFIRMADO`) | spec `document-management` |
| US-12 | Como usuario, quiero descargar el archivo de un documento activo, para trabajar con el PDF u otro formato oficial. | En alcance | spec `document-file-storage` |

## Operador (terminal)

| ID | Historia | Estado | Fuente |
| --- | --- | --- | --- |
| US-13 | Como operador de la instalación, quiero crear el primer administrador con el comando `python -m app.cli create-admin` en la terminal, para poder arrancar el sistema sin cuentas automáticas ni contraseñas en variables de entorno. | En alcance | diseño, ADR-007 |

## Fuera del alcance (no son historias de v1)

Recuperación de contraseña por correo, notificaciones de cambios, registro público, multi-tenant, verificación de cumplimiento, indexación de contenido de archivos: ver `../vision/scope.md`.
