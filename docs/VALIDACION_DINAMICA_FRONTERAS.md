# Validación dinámica de fronteras — CatedralX

> Estado: probes aislados añadidos a CI; no es telemetría de una instancia productiva.
> Rama: `fix/perceive-contract-hardening-20261122`
> Alcance: feedback, gobernanza económica, despacho Agents, DecisionResult y correlación.
> Restricción: no fusionar módulos, no eliminar archivos, no autorizar operaciones reales.

## 1. Método y límites

Se añade `tests/test_runtime_boundary_evidence.py`. Ejecuta funciones reales de escritura/lectura contra JSONL temporales y sustituye únicamente el transporte hacia Agents y el verificador de identidad por dobles sintéticos. No usa los ledgers personales del host, no contacta servicios externos, no mueve dinero, no crea órdenes y no modifica datos de producción.

La evidencia se clasifica así:

- **Runtime aislado:** función real invocada dentro del proceso de prueba y escritura comprobada leyendo el archivo temporal.
- **Simulado:** identidad del aprobador y transporte HTTP a Agents sustituidos por dobles de prueba.
- **Estático:** conclusión derivada de leer la ruta de producción.
- **No demostrado:** requiere observar la instancia real o un consumidor remoto.

Los probes no deben presentarse como prueba de conectividad real con Agents.

## 2. Resultados de los probes

| Frontera | Invocación y escritor observados | Lectura posterior | Resultado |
|---|---|---|---|
| Feedback predictivo | `registrar_prediccion` escribe `feedback.jsonl` | El probe vuelve a leer el JSONL y comprueba `prediction_id` y `cycle_id` | Escritura real en fixture temporal; la predicción no incluye `trace_id` en el payload que construye `REASON.razon.main` |
| Gobernanza económica | `registrar_evento` escribe eventos `measure` y `evaluate` en `impact_cycle.jsonl` | El probe vuelve a leer ambos eventos | Escritura real en fixture temporal; los eventos comparten `cycle_id`, no llevan `trace_id`, y declaran `money_moved=false` |
| Autorización → despacho | `scan_and_dispatch` lee el ledger y escribe `dispatches.jsonl` | El probe vuelve a leer el registro de despacho | Identidad y transporte simulados; el scanner no pasa `traceparent` a `dispatch_task` |
| DecisionResult | `append_result` escribe `results.jsonl` y `get_result` lo lee | El probe comprueba `cycle_id`, `trace_id` y límites de ejecución | Escritura y lectura real en fixture temporal; la traza se conserva dentro de este almacén |

## 3. Hallazgo principal: la traza no cruza todas las fronteras

### 3.1 Feedback predictivo

En `elite/REASON/razon.py`, el diccionario `result` se construye con `cycle_id`, pero `registrar_prediccion(result)` se invoca antes de añadir `trace_id` a ese diccionario. El `DecisionResult` sí recibe el `trace_id` explícito al llamar a `build_decision_result`.

Consecuencia: la predicción y el DecisionResult pueden relacionarse por `cycle_id` cuando ese identificador existe, pero el registro de predicción no conserva la misma traza W3C. El probe deja esta diferencia comprobable.

### 3.2 Gobernanza económica

`registrar_evento` persiste `event_id`, `cycle_id`, tipo de evento, payload y controles. No incluye un campo de traza W3C de primer nivel. Su secuencia contractual es:

`measure → evaluate → propose → authorize → verify → feedback`

La autorización exige una aserción de identidad verificada, un subject coincidente y el permiso `economic_cycle_authorize`. Esto es gobernanza de propuesta, no ejecución de una operación financiera.

### 3.3 Intención de despacho y aceptación remota

`dispatch_authorized_cycles.scan_and_dispatch` llama a `dispatch_task` con clave de idempotencia, pero no entrega un `traceparent` derivado del ciclo de razonamiento. `dispatch_agents.dispatch_task` genera una nueva raíz W3C cuando recibe `traceparent=None`.

El scanner exige `task_id` y `run_id`, y registra la respuesta HTTP `202` como `status=dispatched`. Ese registro prueba que la API aceptó la tarea para procesamiento; no prueba que el worker la ejecutó, que produjo un candidato ni que un verificador independiente lo aceptó.

Además, `dispatch_task` construye la solicitud con `side_effects=none` y success criteria que exigen aceptación independiente. No hay orden financiera habilitada por esta ruta.

### 3.4 Procedencia y aceptación

`MSX.provenance` crea registros de procedencia en memoria; `REASON.orchestrator.execute_cycle` los agrega al estado cognitivo y `contracts.builder.build_decision_result` los proyecta al contrato. `result_store` conserva `cycle_id` y `trace_id`.

El módulo `MSX.cycle_manifest` puede sellar un manifiesto, pero su propia documentación declara que no autoriza ejecución ni sustituye verificación independiente. La ruta one-shot no persiste actualmente un manifiesto de ciclo.

El estado interno `DecisionResult.status=ACCEPTED` significa que la evaluación interna pasó sus condiciones. El propio builder deja como siguiente acción `SOLICITAR_ACEPTACION_INDEPENDIENTE`; por tanto, no es evidencia de aceptación externa.

## 4. Lectores y escritores relevantes

| Artefacto | Escritor observado / identificado | Lectores identificados | Límite |
|---|---|---|---|
| `feedback.jsonl` | `razon.main → registrar_prediccion`; etiquetado por `bin/feedback_label.py` / adaptador FEX | `evaluar_feedback`, `bin/feedback_report.py`, adaptador FEX, ciclo sintético maestro con ruta explícita | Etiquetado por acción explícita; no hay servicio continuo de etiquetado |
| `impact_cycle.jsonl` | `economic_cycle.registrar_evento` | `resumir_ciclos`, `cargar_propuesta_autorizada`, scanner de despacho | El scanner consume autorización; no crea la autorización |
| `dispatches.jsonl` | `dispatch_authorized_cycles._append_jsonl` | `_read_jsonl` para idempotencia | El estado dispatched no es estado de ejecución final |
| `results.jsonl` | `result_store.append_result` | `result_store.get_result` | Append-only; preserva traza y procedencia del contrato |
| `hormonas.json` | `REASON.procesador.TransductorEndocrino.guardar` | `TransductorEndocrino._cargar`, orquestador / Nexus según configuración | Los probes nuevos no ejecutan un ciclo completo de estado hormonal |

## 5. Decisiones conservadoras

1. Mantener feedback predictivo y gobernanza económica separados.
2. Mantener `DecisionResult`, ledger económico, ledger de feedback y log de despacho como artefactos distintos.
3. No interpretar `202` ni `dispatched` como ejecución terminada.
4. No interpretar `DecisionResult.ACCEPTED` como aceptación independiente.
5. No declarar `MSX.cycle_manifest` integrado en la ruta one-shot.
6. No fusionar módulos ni cambiar contratos como parte de estos probes.

## 6. Siguiente corrección propuesta — aún no aplicada

Para lograr correlación verificable sin mezclar responsabilidades:

- Propagar el mismo `trace_id` a la predicción antes de `registrar_prediccion`.
- Añadir `trace_id` opcional y validado a cada evento económico, manteniendo `cycle_id` como clave de negocio.
- Derivar y pasar un `traceparent` W3C al scanner/adaptador de despacho, conservando la relación padre-hijo.
- Mantener estados explícitos y separados para `dispatch_accepted`, `execution_completed`, `candidate_published` y `independent_acceptance`.
- Persistir el manifiesto solo cuando exista una decisión contractual y una prueba de su lector/verificador.

No se aplican estas modificaciones hasta revisar el resultado del probe y su CI. La observación de una instancia productiva requiere ejecutar el mismo protocolo en el host real con sus rutas configuradas y sin sustituir el transporte remoto.
