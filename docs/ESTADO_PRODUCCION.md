# Estado de implementación — Chalamandra Magistral DecoX

**Corte de revisión estática:** 2026-10-26.  
**Alcance:** archivos accesibles en GitHub, configuración versionada y código visible.  
**Fuera de alcance verificado:** procesos, variables reales de entorno, systemd runtime, Cloudflare Tunnel, NSG/firewall, puertos, DNS, secretos desplegados, logs de VM y recorrido HTTP extremo a extremo.

## 1. Veredicto

**No declarar el sistema integrado operativo de extremo a extremo todavía.** CatedralX y componentes parciales del motor de agentes existen en código, pero `main` contiene una regresión P0 en las rutas internas, la aceptación Ed25519 no está conectada y no se confirmó un CI verde reciente del commit actual.

La unidad systemd versionada para la API escucha en loopback y configura `CHALAMANDRA_API_ENABLE_MODEL_CALLS=false`. Eso describe el archivo versionado, no demuestra que el servicio esté activo en la VM.

## 2. Estado de código revisado

| Componente | Estado observado | Evidencia/limitación |
|---|---|---|
| CatedralX determinista | Código presente | `BIN/catedral`, `elite/` y `tests/` existen; no se ejecutó la suite completa en esta revisión. |
| API de agentes | Código presente | `api/server.py` usa JWT y scopes en varias rutas. |
| TaskBus SQLite | Código presente | `api/task_bus.py` implementa reserva e idempotencia. |
| Rutas internas | **P0** | En `main`, GET de runs no comprueba `orchestration:read` y llama `_read_all/_tasks_file` no definidos; POST de resultados no comprueba `tasks:complete`. [PR #13](https://github.com/Chalamandra-Magistral-deco/chalamandra-agent-engine/pull/13) propone corregirlo; sigue en borrador. |
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

1. **P0:** restaurar scopes/autorización y pruebas de rutas internas; usar el TaskBus SQLite canónico.
2. **P1:** unificar el contrato de aceptación e integrar Ed25519, con dependencia declarada y custodia de claves separada.
3. **P1:** corregir/conectar el parser W3C y validar flags/IDs en pruebas.
4. **P1:** recuperar el `.env.example` completo, distinguir variables públicas/privadas y documentar generación de claves.
5. **P1:** corregir scopes de suscripciones, completar el endpoint de alta y endurecer SSRF frente a redirecciones/resolución DNS.
6. Ejecutar suite completa, Ruff, mypy, build y pruebas de integración en el commit exacto.
7. Inspeccionar la VM sin reiniciar ni desplegar: systemd, procesos, sockets, variables sin valores secretos, logs, red y recepción real de trabajos.
8. Validar una sola vertical slice antes de habilitar distribución externa o el modo proactivo.
