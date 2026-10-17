# Casos de prueba

Casos derivados de los escenarios de las tres especificaciones del cambio `dairy-doc-manager` y de las reglas de negocio. Formato GIVEN/WHEN/THEN, alineado con la spec de origen: sirve de puente a las pruebas automatizadas (`00-strategy.md`).

Convención: `TC-nn` · Fuente = requisito de spec o ADR.

## Autenticación y cuentas (spec `user-account-management`)

| ID | Dado | Cuando | Entonces | Fuente |
| --- | --- | --- | --- | --- |
| TC-01 | Un visitante sin sesión | intenta acceder al catálogo | el acceso se rechaza hasta que el inicio de sesión tenga éxito | Authentication Required |
| TC-02 | Un administrador crea una cuenta | se guarda | la cuenta existe y su titular puede iniciar sesión | Account Provisioning |
| TC-03 | Una cuenta activa | el administrador la desactiva | su titular ya no puede iniciar sesión y el registro permanece | Account Provisioning |
| TC-04 | Una cuenta desactivada | el administrador la edita a activa | su titular puede iniciar sesión de nuevo | Account Provisioning |
| TC-05 | Un visitante sin sesión | se inspecciona la aplicación en busca de registro propio | no existe flujo de auto-registro ni de aprobación | Account Provisioning |
| TC-06 | El administrador crea una cuenta | se guarda | lleva exactamente un rol: administrador o usuario normal | Two Roles |
| TC-07 | Un usuario normal autenticado | emite una creación/edición/desactivación de cuenta | la acción se rechaza y ningún dato de cuenta cambia | Authorization Boundary |
| TC-08 | ~100 cuentas provisionadas | sus titulares inician sesión y usan el catálogo | el inicio de sesión y la administración funcionan para todas | Account Capacity |
| TC-09 | Un comando CLI `create-admin` sobre base vacía | se ejecuta | crea un administrador con hash bcrypt | diseño (CLI) |
| TC-10 | La base ya contiene un administrador | se ejecuta `create-admin` sin `--force` | el comando se niega | diseño (CLI) |
| TC-11 | Se ejecuta `create-admin` | se observa la ejecución | la contraseña no aparece en argv, en logs ni se registra sin eco | diseño (Threat Matrix) |

## Documentos (spec `document-management`)

| ID | Dado | Cuando | Entonces | Fuente |
| --- | --- | --- | --- | --- |
| TC-12 | Un usuario normal autenticado | se lista el catálogo | se devuelven todos los documentos no retirados | Shared Catalog |
| TC-13 | Un administrador autenticado | envía un documento nuevo | el registro se guarda y aparece en el catálogo | Admin CRUD |
| TC-14 | Un usuario normal autenticado | intenta crear, actualizar o eliminar | la acción se rechaza y el registro queda intacto | Admin CRUD |
| TC-15 | Un catálogo con documentos | un usuario normal busca | se devuelven los coincidentes; sin coincidencias: vacío, sin error | View/Search/Filter |
| TC-16 | Un documento activo | el administrador lo retira (borrado suave) | ningún listado, búsqueda o filtro lo devuelve a usuarios normales | Soft-Delete |
| TC-17 | Un documento borrado suave | el administrador abre la vista de registros eliminados | el registro figura allí; ninguna vista de usuario normal lo expone | Soft-Delete |
| TC-18 | Un documento borrado suave | el administrador lo restaura | reaparece en el catálogo | Soft-Delete |
| TC-19 | Un administrador ingresa un cuerpo emisor nunca usado | se guarda el registro | ese texto exacto se almacena y se muestra | Free-Text Issuing Body |
| TC-20 | Cualquier pantalla | renderiza | etiquetas, acciones y mensajes están en español neutro | Spanish UI |
| TC-21 | Volumen confirmado sembrado (≥300 docs, 100 usuarios) | corren las consultas de catálogo, búsqueda y filtro | toda columna filtrada está indexada y la revisión registra las medidas | Indexing/Performance |
| TC-22 | El release terminado | se verifica la lista de exclusiones | no existe ninguna funcionalidad excluida; el objetivo móvil usa la misma base de código Python | Scope Exclusions |

## Archivos (spec `document-file-storage`)

| ID | Dado | Cuando | Entonces | Fuente |
| --- | --- | --- | --- | --- |
| TC-23 | Un administrador sube un PDF para un documento | completa la subida | el binario se almacena y se asocia al registro | Admin Upload |
| TC-24 | Un usuario normal autenticado | intenta subir o reemplazar un archivo | el intento se rechaza y no se almacena binario | Admin Upload |
| TC-25 | Un archivo almacenado y un usuario con sesión | solicita ese archivo | se devuelve el contenido almacenado | File Serving |
| TC-26 | Un visitante sin sesión | solicita un archivo | la petición se rechaza | File Serving |
| TC-27 | Un usuario normal autenticado viendo un documento activo | solicita la descarga | recibe el binario del archivo | Normal-User Download |
| TC-28 | Un documento retirado (borrado suavo) | un usuario normal solicita su archivo | la descarga se rechaza (404) | Normal-User Download |
| TC-29 | Cientos de archivos almacenados | usuarios autenticados los recuperan | cada archivo se devuelve íntegro | Storage at Volume |
| TC-30 | Un archivo que excede el límite / un tipo fuera de lista | se intenta la subida | 413 / 415 respectivamente; nada se almacena | diseño (API) |

## Complemento de integración (diseño)

Los siguientes aspectos se prueban como parte del nivel de integración (Testing Strategy del diseño) y refuerzan los casos anteriores: 401 anónimo en todas las rutas; 403 de usuario normal en **cada** ruta de administrador; logout elimina la sesión; cuenta desactivada rechazada en el siguiente request; sin escape de ruta en subida.
