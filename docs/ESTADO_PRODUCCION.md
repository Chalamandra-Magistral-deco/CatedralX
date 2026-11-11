# Estado de implementación — CatedralX

**Actualizado:** 2026-11-11  
**Fuente de verdad:** rama main de Chalamandra-Magistral-deco/CatedralX.  
**Commit inspeccionado:** 2ec860337285b6054bbd0e2b44678c42a769f136.

## Estado vigente verificado

- GitHub Actions del commit inspeccionado: unit-tests y Build and smoke-test the CLI image completados correctamente.
- Suite: **354 pruebas aprobadas**.
- pip check: correcto.
- compileall: correcto.
- Imagen Docker: build y smoke test CLI correctos.
- cryptography==50.0.2: declarada en requirements.txt y fijada en requirements.lock.
- Árbol Git: 213 entradas, no truncado.
- Ramas visibles al corte: main, chore/catedralx-repo-hygiene-20261111 y docs/catedralx-host-neutral-status-20261111. Las dos ramas de trabajo divergen de main; sus cambios visibles son de higiene de dependencias/CI y documentación. No se han eliminado.
- VM anterior: fuera del plan operativo. No usarla como fuente de estado ni destino.
- No hay evidencia de runtime nuevo ni integración end-to-end activa. CI verde acredita el commit y el artefacto construido, no despliegue, conexión con Agents ni operación real.
- Seguridad: revisión estática parcial; consultar docs/SEGURIDAD_REPOSITORIO.md. No se certifica ausencia de secretos en el historial ni estado de Secret Scanning.
- Documentación histórica: clasificada y preservada según docs/INDICE_DOCUMENTAL_Y_GOBIERNO.md.

## Veredicto

**Repositorio validado por CI; integración y operación end-to-end no verificadas; seguridad histórica pendiente de cierre.** No etiquetar CatedralX como producción operativa ni como libre de secretos con la evidencia disponible.

## Alcance y límites

La revisión cubre el árbol GitHub de main, archivos versionados, workflows, dependencias y ejecución CI del commit identificado. No cubre runtime desplegado, procesos, servicios, DNS, red, endpoints activos, valores de variables de entorno, secretos de proveedores, alertas nativas de Secret Scanning ni análisis completo de todos los objetos y refs del historial.

## Documentos de referencia

- Índice y conservación: docs/INDICE_DOCUMENTAL_Y_GOBIERNO.md.
- Seguridad: docs/SEGURIDAD_REPOSITORIO.md.
- Arquitectura: docs/ARQUITECTURA_OBJETIVO.md.
- Contratos: docs/contracts/README.md.

---

## Registro histórico preservado — corte 2026-10-26

El texto siguiente se conserva como registro de una auditoría anterior. Sus afirmaciones sobre VM, servicios, integración, dependencias, aceptación y pruebas no representan el estado vigente al 2026-11-11. Se mantiene para trazabilidad y no debe utilizarse como instrucción operativa actual.

## 1. Veredicto

**No declarar el sistema integrado operativo de extremo a extremo todavía.** La regresión P0 de autorización fue corregida y fusionada en `aee4e114ecdc86d9ff8abade69e02799b500d90e`; pruebas, Ruff, mypy y smoke test de imagen pasaron. La aceptación Ed25519 no está conectada y el recorrido real en VM sigue sin verificarse.

La unidad systemd versionada para la API escucha en loopback y configura `CHALAMANDRA_API_ENABLE_MODEL_CALLS=false`. Eso describe el archivo versionado, no demuestra que el servicio esté activo en la VM.

## 2. Estado de código revisado

| Componente | Estado observado | Evidencia/limitación |
|---|---|---|
| CatedralX determinista | Código presente | `BIN/catedral`, `elite/` y `tests/` existen; no se ejecutó la suite completa en esta revisión. |
| API de agentes | Código presente | `api/server.py` usa JWT y scopes en varias rutas. |
| TaskBus SQLite | Código presente | `api/task_bus.py` implementa reserva e idempotencia. |
| Rutas internas | **P0** | Corregido en `main` por commit `aee4e114ecdc86d9ff8abade69e02799b500d90e`: GET de runs comprueba `orchestration:read` y usa `task_bus.get_run_tasks()`; POST de resultados comprueba `tasks:complete`. CI completo del PR pasó, pero la VM no se ha revalidado. |
| Worker | Parcial | `api/worker_loop.py` invoca CatedralX mediante ruta fija. No se encontró una unidad worker en los archivos systemd revisados ni se comprobó el proceso de la VM. |
| Aceptación | Parcial | HMAC-SHA256 y comprobación de digest existen; el helper Ed25519 no está integrado al gate. |
| Distribución | Parcial | Store/dispatcher existen; creación de suscripciones y ciclo completo de eventos requieren cerrar el contrato. |
| Trazabilidad W3C | Parcial | Existe `api/trace_parser.py`, pero el servidor no llama al helper. Las reglas y flags deben validarse antes de decir “estricto”. |
| CI | Sin veredicto final | No se dispone de una ejecución completa reciente consultable del commit actual; no se presume verde. |
| VM y red | No verificado | La lectura del repositorio no confirma servicios, túnel, DNS, puertos, variables o entrega real. |

## 3. Límites de confianza

- Mantener `CHALAMANDRA_API_ENABLE_MODEL_CALLS=false` por defecto; no activarlo para completar la arquitectura.
- API, worker y generador de candidatos no pueden usar la autoridad del verificador independiente.
- La clave privada Ed25519 debe residir exclusivamente en el proceso autorizado de firma/verificación; la API receptora valida con la clave pública.
- El endpoint de resultados del worker exige un token de servicio y scope explícito aunque el listener esté en loopback.
- Resultados pendientes, bloqueados, rechazados o inciertos no se publican como aceptados.
- No copiar, imprimir ni guardar secretos reales en Git.

## 4. Snapshot operativo anterior

Un documento fechado 2026-10-25 afirmaba que API, worker, túnel Cloudflare y dominio estaban activos, y citaba conteos de pruebas. **Esas afirmaciones no se revalidaron aquí y no deben usarse como confirmación del estado actual.** Para validarlas hay que inspeccionar la VM autorizada y comprobar systemd, procesos, configuración sin volcar secretos, logs, endpoints y una solicitud de prueba.

## 5. Secuencia de remediación

1. **P0 resuelto en código:** confirmar en la VM autorizada que el despliegue usa el commit fusionado y probar las rutas internas con tokens de scopes correctos/incorrectos.
2. **P1:** unificar el contrato de aceptación e integrar Ed25519, con dependencia declarada y custodia de claves separada.
3. **P1:** corregir/conectar el parser W3C y validar flags/IDs en pruebas.
4. **P1:** recuperar el `.env.example` completo, distinguir variables públicas/privadas y documentar generación de claves.
5. **P1:** corregir scopes de suscripciones, completar el endpoint de alta y endurecer SSRF frente a redirecciones/resolución DNS.
6. Ejecutar suite completa, Ruff, mypy, build y pruebas de integración en el commit exacto.
7. Inspeccionar la VM sin reiniciar ni desplegar: systemd, procesos, sockets, variables sin valores secretos, logs, red y recepción real de trabajos.
8. Validar una sola vertical slice antes de habilitar distribución externa o el modo proactivo.
