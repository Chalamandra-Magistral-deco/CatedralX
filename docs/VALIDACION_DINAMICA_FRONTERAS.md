# Validación dinámica de fronteras — CatedralX

> Estado: validación aislada de escrituras/lecturas y propagación W3C en CI; no es telemetría de una instancia productiva.
> Rama: `fix/perceive-contract-hardening-20261122`
> Alcance: feedback, gobernanza económica, despacho Agents, DecisionResult y correlación.
> Restricción: no fusionar módulos, no eliminar archivos, no autorizar operaciones reales.

## 1. Método y límites

Los probes de `tests/test_runtime_boundary_evidence.py` ejecutan funciones reales de escritura/lectura contra JSONL temporales. Sustituyen únicamente el transporte hacia Agents y el verificador de identidad por dobles sintéticos. No usan los ledgers del host, no contactan servicios externos, no mueven dinero, no crean órdenes y no modifican datos de producción.

La corrección de propagación añade el mismo `trace_id` W3C al registro de predicción, a cada evento del ledger económico y al `traceparent` enviado al adaptador de Agents. En cada salto HTTP se genera un nuevo `parent-id` de 16 bytes, manteniendo el `trace-id` de 16 bytes original. Los ciclos históricos sin traza siguen siendo válidos y conservan el comportamiento previo: Agents genera una nueva raíz.

## 2. Evidencia y resultados

| Frontera | Comportamiento corregido | Protección |
|---|---|---|
| Feedback predictivo | `razon.main` añade `trace_id` antes de llamar a `registrar_prediccion` | El probe vuelve a leer el JSONL y verifica igualdad de `cycle_id` y `trace_id` |
| Gobernanza económica | `registrar_evento` persiste `trace_id` opcional en el nivel del evento; las etapas posteriores heredan la traza del ciclo y rechazan una traza diferente | El probe vuelve a leer measure/evaluate y verifica la misma traza y `money_moved=false` |
| Autorización → despacho | `cargar_propuesta_autorizada` devuelve la traza del ciclo tras verificar que no hay trazas contradictorias; el scanner construye un `traceparent` con esa traza y un parent-id nuevo | El probe verifica que el transporte simulado recibe la traza upstream; el adaptador conserva validación W3C |
| DecisionResult | El almacén mantiene `cycle_id` y `trace_id` | El probe comprueba append y read-back |

Los campos de traza son metadatos de correlación. No cambian la autoridad de los eventos, no sustituyen la firma del aprobador y no autorizan efectos externos.

## 3. Fronteras que siguen separadas

### 3.1 Feedback predictivo frente a gobernanza económica

El ledger de feedback conserva predicciones y resultados observados para evaluación offline. El ledger económico conserva medición, evaluación, propuesta, autorización, verificación y feedback gobernado. La nueva traza correlaciona ambos dominios cuando el mismo ciclo la transporta, pero no combina sus esquemas, escritores ni lectores.

### 3.2 Intención frente a ejecución

El scanner solo despacha propuestas con autorización válida y clave de idempotencia. El HTTP `202` sigue indicando aceptación de la tarea por la API, no ejecución completada, publicación de candidato ni aceptación independiente. El `traceparent` permite correlación distribuida; no cambia ese significado.

### 3.3 Procedencia frente a autorización y aceptación

`DecisionResult`, el ledger económico, el ledger de feedback y el log de despacho siguen siendo artefactos distintos. `DecisionResult.ACCEPTED` es un veredicto interno. La aceptación independiente debe conservar evidencia separada.

## 4. Compatibilidad y controles

- `trace_id` es opcional para ciclos históricos y llamadas existentes.
- Cuando un ciclo ya tiene traza, las etapas posteriores heredan esa traza si el caller no proporciona una.
- Si se proporciona otra traza o el ledger contiene trazas contradictorias, la operación falla cerrada.
- Los eventos económicos siguen pasando por la misma máquina de estados, verificación de identidad, digest de evidencia y nonce.
- La traza no se incluye en la autorización como permiso ni altera el conjunto de operaciones permitidas.
- No se fusionan ledgers, módulos o estados de aceptación.

## 5. Lo que todavía no queda demostrado

Los probes usan un transporte simulado. No prueban que el servicio Agents real conserve el contexto W3C en sus workers, ni que el candidato final y la aceptación independiente se puedan recuperar con el mismo `trace_id`. Tampoco prueban una instancia productiva de `hormonas.json` o snapshots. Esa fase requiere instrumentación del runtime real, lectura de logs de ambos servicios y correlación de `trace_id`, `run_id`, `task_id` y candidate/acceptance IDs.

No se han fusionado módulos, desplegado servicios ni ejecutado órdenes.
