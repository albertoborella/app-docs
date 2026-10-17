# Reglas de negocio

Políticas inquebrantables del dominio, derivadas de las especificaciones y decisiones confirmadas del cambio `dairy-doc-manager`. Cada regla es la fuente de verdad para los casos de prueba (`../testing/01-test-cases.md`).

## Autoría y permisos

| ID | Regla | Fuente |
| --- | --- | --- |
| BR-01 | Solo el administrador crea, modifica y elimina documentos. Cualquier intento de escritura de un usuario normal se rechaza y el registro queda intacto. | spec `document-management` |
| BR-02 | Solo el administrador crea, edita y desactiva cuentas de usuario. Un usuario normal que intente gestión de cuentas es rechazado sin cambio de datos. | spec `user-account-management` |
| BR-03 | El sistema tiene exactamente dos roles; cada cuenta posee exactamente uno, asignado al provisionarla. | spec `user-account-management` |
| BR-04 | No existe auto-registro ni flujo de aprobación de cuentas en ninguna parte del sistema. | spec `user-account-management` |

## Estados de cuenta

| ID | Regla | Fuente |
| --- | --- | --- |
| BR-05 | Una cuenta desactivada no puede iniciar sesión; su registro permanece en el sistema. | spec `user-account-management` |
| BR-06 | Editar una cuenta desactivada a activa vuelve a permitir el inicio de sesión. | spec `user-account-management` |
| BR-07 | La desactivación también invalida las sesiones vigentes de esa cuenta en su siguiente petición. | diseño, ADR-002 |
| BR-08 | El primer administrador de una instalación fresca se crea únicamente con el comando de terminal `python -m app.cli create-admin`; no se crea ninguna cuenta automáticamente. | diseño, ADR-007 |

## Documentos y borrado suave

| ID | Regla | Fuente |
| --- | --- | --- |
| BR-09 | Retirar un documento obsoleto es un borrado suave (`deleted_at` con marca de tiempo): el registro sale del catálogo para todos los usuarios normales, permanece en la base de datos y es visible únicamente en la papelera del administrador. | spec `document-management`, ADR-005 |
| BR-10 | Un documento retirado puede restaurarse; al hacerlo reaparece en el catálogo. | spec `document-management` |
| BR-11 | No existe borrado físico (hard delete) en la API ni en la interfaz de v1. | spec, ADR-005 |
| BR-12 | No existe un estado "obsoleto" visible para el usuario normal: retirado equivale a invisible en todo listado, búsqueda y filtro. | spec `document-management` |
| BR-13 | El cuerpo emisor es texto libre introducido por el administrador; cualquier valor nuevo se guarda y se muestra tal cual. No hay catálogos codificados de tipos de documento ni de jurisdicciones. | spec `document-management` |
| BR-14 | El catálogo es único y compartido: no se particiona por empresa ni tenant; todo documento no retirado aparece para cualquier usuario autenticado. | spec `document-management` |

## Archivos

| ID | Regla | Fuente |
| --- | --- | --- |
| BR-15 | Subir y reemplazar archivos es exclusivo del administrador; el usuario normal no sube ni reemplaza binarios. | spec `document-file-storage` |
| BR-16 | Cada documento admite como máximo un archivo vigente: el reemplazo sobrescribe el binario en el lugar; no hay versionado de archivos en v1. | diseño, ADR-004 |
| BR-17 | Los formatos admitidos son una lista de permitidos (PDF, DOCX, XLSX, ODT, PNG, JPG) con un límite de tamaño — `CONFIRMADO` (usuario): 25 MB. Tipos fuera de la lista → 415; excede el límite → 413. | diseño |
| BR-18 | El servidor genera todas las rutas de almacenamiento; los nombres de archivo del cliente nunca tocan el sistema de archivos. | diseño, ADR-004 |
| BR-19 | Un usuario normal no puede descargar el archivo de un documento retirado (recibe 404, sin fuga de existencia); el administrador sí puede consultarlo desde la papelera. | spec `document-file-storage`, diseño |

## Acceso y catálogo

| ID | Regla | Fuente |
| --- | --- | --- |
| BR-20 | Todo acceso al catálogo y a los archivos exige sesión iniciada; las peticiones anónimas se rechazan (401). | spec `user-account-management` |
| BR-21 | La interfaz se muestra íntegramente en español neutro: etiquetas, acciones y mensajes en todas las pantallas y objetivos (web, escritorio, móvil). | spec `document-management` |
| BR-22 | Se permiten varias cuentas de administrador (modelo de dos roles) — `CONFIRMADO` (usuario). Si en el futuro se exigiera un único administrador, sería un cambio aditivo (guardia o índice único parcial). | diseño, ADR-006 |
