# Contratos OpenAPI — Chalamandra Magistral DecoX

**Revisión histórica:** 2026-10-28 (checkout de trabajo). **Actualización de vigencia:** 2026-11-11. Este README y sus YAML son contratos/especificaciones; no demuestran que Agents esté desplegado o conectado.

El código versionado y el estado de contenedores se documentan por separado; los contratos se contrastan con agents/`api/server.py`, no se asume conformidad por similitud de nombres.
Los contratos describen el comportamiento deseado; tener rutas con nombres similares no prueba conformidad ni despliegue.

| Contrato | Función objetivo | Estado observado |
|---|---|---|
| `request_flow.yaml` | Crear trabajos, consultar estado y recuperar resultados aceptados. | Implementación en Agents; el payload exige `current_price`, `observed_at` con zona horaria y `source`; si `data_source=provided`, también exige al menos 30 `historical_prices`. El recorrido end-to-end debe validarse contra el commit y la imagen que se liberen. |
| `distribution_flow.yaml` | Suscripciones y distribución de resultados aceptados. | Rutas GET/POST/DELETE /v1/subscriptions y POST /internal/v1/distributions presentes según el corte histórico. Solo se admite `result.accepted`; no se ofrecen suscripciones a `result.blocked` porque no existe entrega automática garantizada para ese evento. Respuestas documentadas: 202 dispatched/already_dispatched, 409 en conflicto/en progreso y 502/503 ante entrega no satisfactoria o indisponibilidad. |
| `orchestration_flow.yaml` | Disparar runs, consultar estado y recibir resultados del worker con token de servicio. | Rutas presentes en `api/server.py`; el token de servicio de CatedralX exige scope y subject. La existencia de la ruta no demuestra que el scheduler esté desplegado ni habilitado. |

## Componentes relacionados

- **TaskBus:** SQLite, reserva de tareas e idempotencia existen en `api/task_bus.py`.
- **Candidate store:** persiste candidatos y calcula un digest SHA-256 de evidencia.
- **Acceptance store:** `api/acceptance_store.py` persiste decisiones append-only y valida firma/digest Ed25519 mediante la clave pública configurada. La semilla de firma privada no debe residir en la API ni en el worker ordinario.
- **Ed25519:** `api/crypto_signer.py` verifica con nacl.signing.VerifyKey; `verifier/independent_acceptance_verifier.py` es el firmador independiente que custodia la semilla fuera de la API. Confirmar que los entornos y volúmenes reales mantienen esa separación antes de liberar.
- **Worker:** `api/worker_loop.py` existe y `chalamandra-worker.service` se encontró activo/habilitado en la VM el 2026-10-28; corre desde el checkout de trabajo, por lo que su versión puede diferir de la imagen del API en Docker.
- **Modo proactivo:** existe `elite/bin/dispatch_authorized_cycles.py` para escanear ciclos elegibles una vez. No hay timer de CatedralX/feedback/dispatch habilitado confirmado; no inferir planificación periódica a partir del script.

## Criterio de finalización

Un flujo solo pasa a “validado” cuando el endpoint comprueba el scope correcto, el payload satisface el schema, el recorrido se ejecuta de extremo a extremo, IDs/evidencia/digest/aceptación son coherentes, el CI está verde en el commit exacto y el despliegue real se inspecciona. No declarar los tres contratos implementados solo porque existan rutas o módulos.


## Vigencia y límites — 2026-11-11

Las menciones a VM, procesos systemd y estado activo de 2026-10-28 son evidencia histórica y no describen un runtime vigente. La VM anterior está fuera del plan operativo. La integración con Agents debe verificarse desde ambos repositorios y en un entorno actual antes de marcar Request, Distribution u Orchestration como end-to-end. Consulta [estado vigente](../ESTADO_PRODUCCION.md) y [índice documental](../INDICE_DOCUMENTAL_Y_GOBIERNO.md).

## Reglas normativas de los contratos — 2026-11-11

- **Request payload:** `current_price`, `observed_at` (ISO-8601 con zona horaria) y `source` son obligatorios. `historical_prices` es obligatorio cuando `data_source=provided` y contiene al menos 30 observaciones positivas. `source` es metadato declarado, no prueba criptográfica de procedencia.
- **Distribution:** solo `result.accepted` es un evento distribuible. Un resultado candidato, bloqueado, incierto o rechazado no se publica como aceptado ni genera webhook de aceptación.
- **DecisionResult:** el esquema interno de `elite/contracts/schemas/decision_result.json` representa estados internos (`ACCEPTED`, `UNCERTAIN`, `REJECTED`, `BLOCKED_MISSING_INPUT`). El contrato de lectura pública Request usa `status=accepted`; el adaptador debe traducir explícitamente `ACCEPTED → accepted`. Esa traducción no está demostrada por el repositorio CatedralX y queda pendiente de verificar en Agents. El endpoint público solo debe exponer resultados aceptados y conservar `analysis_only=true`, `orders_created=false`, `orders_executed=false`. No intercambiar ni equiparar ambos esquemas.
- **Orchestration acceptance:** `AcceptanceDecision` requiere identidad del verificador, digest SHA-256, algoritmo Ed25519, firma Base64 y fecha de decisión. La implementación debe verificar identidad, firma y digest antes de registrar aceptación. El esquema exige evidencia de firma, pero este YAML no acredita que la verificación esté desplegada.
- **Orchestration run state:** `RunStatus` admite `queued`, el mismo estado que devuelve `RunAccepted`, además de estados terminales y de bloqueo.
- **Gate del ciclo sintético:** `risk_gate.independent=true` en `elite/REASON/core_contract.py` es una afirmación recibida por el constructor, no una verificación criptográfica. La aceptación independiente debe comprobarse en una frontera separada; el constructor no puede certificarla por sí mismo.


## Dimensiones centrales y unidades

- `CENTRAL_DIMENSIONS_BP` contiene únicamente `viability_bp`, `human_value_bp`, `distribution_bp`, `resilience_bp` y `evidence_bp`. Cada valor debe ser un entero entre 0 y 10000.
- `viability_bp` no se deriva de BUY/SELL/HOLD. La dirección del mercado no es una medición de viabilidad económica.
- `reinvestment_surplus` es una cantidad monetaria decimal, no basis points; su única fuente de entrada es `DYNAMIC_CONSTRAINTS.reinvestment_surplus`. La regla central y la restricción dinámica consumen ese mismo campo para evitar dos valores discrepantes.
- La fórmula dinámica `surplus >= entropy_time_scale * entropy_rate` requiere definición de unidades, periodo, moneda y método de calibración antes de interpretarse como umbral económico validado. La CI verifica implementación y fail-closed, no validez dimensional ni predictiva.
- En `DYNAMIC_CONSTRAINTS`, `dominant_signal_weight` y `minimum_confidence` son campos opcionales validados cuando se suministran, pero no participan actualmente en `growth_allowed`. `degradation_rate` y `accumulated_noise` se conservan como observaciones; no activan recalibración ni bloqueo por sí solos. No presentarlos como métricas ya calibradas.
- `uncertainty` del ciclo sintético acepta cualquier número finito no negativo; su unidad, normalización y umbral no están fijados por este contrato. No compararlo con porcentajes o probabilidades.
