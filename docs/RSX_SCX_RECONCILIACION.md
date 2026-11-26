# Reconciliación RSX–SCX: percepción, contrato y entrada al razonamiento

> **Revisión 2 — impacto de consumidores.** Auditoría estática de la rama `docs/canonical-architecture-20261123`. Se ampliaron las búsquedas de llamadas y se inspeccionaron los consumidores productivos y pruebas identificables. No se ejecutaron módulos, tareas, tests ni CI. No se modificó código funcional.

## 1. Alcance y método

Se inspeccionaron:
- `elite/PERCEIVE/stream_altar.py`, `sensors.py`, `data_feeder.py`, `snapshot_signing.py`, `api_pulse.py`, `percepcion.py`, `bunker.py`.
- `elite/REASON/schemas.py`, `razon.py`, `orchestrator.py`.
- `elite/bin/feed_once.py`, `elite/bin/feedback_label.py`.
- Pruebas `test_snapshot_signature.py`, `test_snapshot_freshness.py`, `test_trace_propagation.py`, `test_dynamic_constraints.py`, `test_acceptance_contract.py`, además de búsquedas de referencias para `write_observation`, `from_snapshot`, `construir_sensory_input`, `SensoryInput` y `execute_cycle`.

La búsqueda de código de GitHub y la lectura de archivos son evidencia estática de la rama. No prueban qué proceso está activo en un host, qué configuración está cargada ni qué volumen de observaciones circula en producción.

## 2. Mapa de consumidores encontrado

| Entrada / contrato | Consumidores localizados | Validación antes de razonar |
|---|---|---|
| `write_observation` | `feed_once.main`; `stream_altar.run_once` y `accept_observation` a través de callback; pruebas de firma | El fetcher canónico Binance produce source y observed_at. Los adaptadores genéricos aceptan payloads del caller y delegan al writer |
| `validate_snapshot_payload` | `razon.main`, `BunkerDaemon._ciclo`, `Orchestrator.bucle_infinito`, `feedback_label.main` | Sí, explícita en las cuatro rutas identificadas |
| `from_snapshot` | `razon.main`, `BunkerDaemon._construir_entrada`; pruebas | En los dos entrypoints productivos identificados se llama después de validar el snapshot |
| `construir_sensory_input` | `from_snapshot`; pruebas y utilidades de construcción | Normaliza el payload, pero no verifica firma ni frescura |
| `Orchestrator._construir_sensory_input` | `Orchestrator.bucle_infinito`; pruebas | El bucle valida el snapshot antes de invocar el constructor |
| `SensoryInput` | Constructor de percepción, constructor alternativo del orquestador y llamadas directas de pruebas | Es un dataclass de datos de razonamiento; no incorpora por sí solo procedencia autenticada |
| `execute_cycle` | `razon.main`, Bunker, bucle infinito del orquestador y pruebas | Valida el formato de trace_id y genera uno si no se suministra; no deduplica observaciones |

No se encontró en las búsquedas de código otro consumidor productivo directo de `write_observation` o `from_snapshot` dentro de esta rama. La búsqueda indexada no sustituye una búsqueda exhaustiva en clones, extensiones externas o repositorios distintos.

## 3. Hechos observados y matices corregidos

### 3.1 Productor y writer RSX

1. `stream_altar.build_observation_from_klines` genera explícitamente `source` y `observed_at` a partir de velas cerradas de un minuto. Verifica orden, unicidad, continuidad, precios positivos/finito, al menos 30 velas y antigüedad máxima de 120 segundos.
2. `feed_once.main` utiliza ese fetcher Binance y entrega la observación a `write_observation`.
3. `stream_altar.run_once` y `accept_observation` permiten inyectar fetcher/writer; no restringen el payload a la salida del fetcher Binance.
4. `sensors.normalize_market_payload`, usado por `write_observation`, permite que `observed_at` falte y sustituye source ausente por `"unspecified"`. Si observed_at está presente, valida que sea texto no vacío, pero no exige allí formato ISO ni zona horaria.
5. `write_observation` firma el envelope si la configuración exige firma y lo persiste mediante archivo temporal, fsync y replace atómico. No aplica antes de escribir la allowlist de source ni la regla de frescura del consumidor.
6. El lector `validate_snapshot_payload` sí exige observed_at con zona horaria y frescura máxima de 120 s. Cuando la firma es requerida, exige source permitido y HMAC válido.
7. Por tanto, el hallazgo RSX-01 se precisa: **el adaptador canónico Binance produce los campos requeridos; la brecha está en el contrato genérico del writer/adaptadores**. Un caller genérico puede escribir un snapshot firmado que luego el lector rechaza por timestamp ausente/inválido o source no permitido. No es correcto afirmar que el camino normal `feed_once → Binance` omite esos campos.

### 3.2 Frontera de validación y conversión

8. `from_snapshot` valida la forma del envelope y campos de gobernanza, y construye `SensoryInput`; no ejecuta por sí misma validación de HMAC, allowlist o frescura.
9. En los dos consumidores productivos directos identificados, `razon.main` y `BunkerDaemon._ciclo`, `validate_snapshot_payload` se ejecuta antes de `from_snapshot`.
10. Existe una tercera ruta de ciclo continuo: `Orchestrator.bucle_infinito` valida primero con `validate_snapshot_payload` y luego utiliza su constructor propio `_construir_sensory_input`, no `from_snapshot`.
11. `feedback_label.main` también valida el snapshot antes de registrar el outcome de feedback.
12. Por tanto, RSX-02 es **un riesgo de encapsulación/API y de futuros consumidores**, no evidencia de un bypass en los entrypoints productivos actuales inspeccionados. La secuencia de validación está repetida en varios entrypoints; el constructor público no expresa en su tipo que requiere un snapshot previamente validado.

### 3.3 Procedencia en SCX/MSX

13. `SensoryInput` transporta precios, gap, inercia, free_energy_prev y campos de gobernanza; no tiene campos tipados para `source`, `observed_at`, `observation_id`, hash del snapshot ni resultado de verificación.
14. `razon.main` conserva `observed_at` y `market_source` en su resultado de salida. Eso no significa que estos campos viajen por el contrato `SensoryInput` ni que todas las rutas de ciclo tengan la misma evidencia.
15. El orquestador agrega procedencia de ciclo RSX/SCX/DSX y trace/cycle IDs; el registro de procedencia inspeccionado no demuestra que el hash de snapshot y el source/time originales estén ligados de forma uniforme al resultado de cada entrypoint.

### 3.4 Trazabilidad e idempotencia

16. `razon.main` toma `CATEDRALX_TRACE_ID` o crea un UUID hexadecimal, lo pasa a `execute_cycle` y lo incorpora al resultado y `DecisionResult`.
17. `execute_cycle` genera un trace ID si no se proporciona, valida 32 caracteres hexadecimales minúsculos distintos de cero y agrega trace/cycle a procedencia MSX.
18. Bunker llama `execute_cycle(sensory)` sin trace explícito; recibe un trace generado por el orquestador en el estado, pero el resumen `REASON` que construye no incluye `trace_id`. El resumen se añade a una copia en memoria y el código inspeccionado no persiste ese snapshot modificado.
19. `Orchestrator.bucle_infinito` también llama `execute_cycle(entrada)` sin trace explícito y solo imprime decisión y Hurst; no emite un identificador de traza en ese mensaje.
20. Bunker consulta cada 15 segundos y el bucle del orquestador cada 3 segundos. Ambos pueden volver a procesar el mismo snapshot mientras siga fresco. El writer no asigna `observation_id`; las rutas no consultan un registro durable de observaciones ya procesadas.
21. El trace ID identifica/correlaciona una ejecución; no es una clave idempotente para una observación. Un mismo snapshot puede generar varios cycle IDs, trace IDs, consumos de presupuesto y resultados.

## 4. Discrepancias y correcciones propuestas

| ID | Prioridad | Hallazgo preciso | Riesgo | Corrección propuesta |
|---|---|---|---|---|
| RSX-01 | Alta | El writer genérico acepta timestamp ausente y source por defecto `unspecified`; el fetcher Binance canónico sí proporciona ambos | Writer puede persistir datos que luego rechaza el lector; error diferido y contrato asimétrico | Validar en el writer de producción timestamp con zona horaria y source permitido; aislar explícitamente fixtures/synthetic test |
| RSX-02 | Media | `from_snapshot` no verifica firma/frescura, aunque los entrypoints productivos directos identificados sí validan antes | Un nuevo caller puede saltarse el control por uso incorrecto de una API que acepta payload crudo | Separar tipo/constructor de snapshot crudo y snapshot validado; exponer una única frontera validada sin duplicar verificaciones |
| RSX-03 | Media | `SensoryInput` no transporta source, observed_at, observation_id ni hash/verificación del snapshot | Se pierde procedencia de la observación en el contrato común de razonamiento | Agregar metadatos inmutables tipados o una referencia a registro RSX inmutable, y enlazarla al resultado MSX |
| SCX-01 | Media | One-shot, Bunker y bucle continuo no emiten la misma evidencia de traza en su salida | Correlación operativa desigual entre entrypoints aunque el motor genere trace ID | Definir contrato común de salida con trace_id, cycle_id y referencia de observación; mantener IDs distintos por ejecución |
| SCX-02 | Alta | No hay observation_id ni deduplicación durable; Bunker/bucle pueden volver a consumir el mismo snapshot | Reprocesamiento y gasto repetido mientras el snapshot siga fresco; resultados duplicados | Definir identidad estable de observación y política de replay/deduplicación durable antes de afirmar idempotencia |
| SCX-03 | Baja | La validación está distribuida entre varios entrypoints y constructores con distintas responsabilidades | Deriva futura de reglas y cobertura de pruebas desigual | Centralizar el boundary de validación y exigir que solo un valor validado alcance el constructor de SCX |

## 5. Pruebas existentes y brechas

### Ya identificadas en el repositorio

- `test_snapshot_signature.py`: firma válida, firma ausente, manipulación de precio/source, source no permitido, clave incorrecta/no conocida, envelope malformado, unsigned mode y escritura con permisos restringidos.
- `test_snapshot_freshness.py`: timestamp ausente, sin zona horaria, futuro, antiguo; entrypoints one-shot y Bunker rechazan snapshots caducados; Bunker no sobrescribe el snapshot original.
- `test_trace_propagation.py`: trace explícito, trace generado, rechazo de IDs inválidos y procedencia/ciclo.
- `test_acceptance_contract.py`: validación sintética, rechazo de datos caducados y prueba de entrypoints.
- `test_dynamic_constraints.py`: transporte de campos de gobernanza a `SensoryInput` y rechazo de claves no canónicas.

### No se encontró cobertura específica para

1. Writer genérico → lector: timestamp ausente, timestamp sin zona horaria, source ausente/no permitido; comprobar que el productor rechaza antes de persistir, no que el lector lo rechaza después.
2. Paridad de contrato de salida entre one-shot, Bunker y bucle continuo, incluyendo trace ID y referencia de observación.
3. Correlación del hash/HMAC y source/time originales hasta la procedencia de resultado común de MSX.
4. Reprocesamiento del mismo observation_id: segundo intento, concurrencia, crash-window y recuperación.
5. Política de retención de claves de deduplicación y tratamiento explícito de replay autorizado.

La ausencia se refiere al conjunto de pruebas inspeccionado, no a toda prueba posible en ramas o repositorios no consultados.

## 6. Contrato mínimo propuesto (no implementado)

Para la frontera RSX → SCX se recomienda versionar un envelope con:

- `schema_version`: versión explícita.
- `observation_id`: identidad estable de la observación lógica, estable ante reintentos.
- `source`: productor permitido.
- `observed_at`: tiempo de mercado con zona horaria.
- `received_at`: tiempo de recepción local, separado del tiempo observado.
- `snapshot_hash`: hash del envelope canónico; mantener separado del estado de verificación de firma.
- `signature_status`: resultado de verificación, no un booleano aportado por el caller.
- `payload`: precios/features validados y sus semánticas.
- `trace_id`: contexto de correlación de ejecución, distinto de observation_id.
- `cycle_id`: identidad del ciclo de razonamiento, distinta de ambas.
- `validation_policy_version`: política de frescura, allowlist y validador aplicado.

Estos campos son una propuesta; no se afirma que ya existan en código. El hash por sí solo no autentica el productor; la firma HMAC actual es una verificación con secreto compartido y la allowlist limita las fuentes admitidas.

## 7. Hipótesis, datos ausentes y aspectos por validar

**Hechos observados:** existen tres rutas de ciclo (one-shot, Bunker y bucle continuo); las tres rutas identificadas validan el snapshot antes de razonar. El writer genérico es menos estricto que el lector. No hay observation_id en el envelope inspeccionado.

**Hipótesis:** Bunker y/o el bucle continuo pueden estar activos en alguna instalación. El repositorio no demuestra que estén desplegados ni ejecutándose.

**Datos ausentes:** telemetría runtime, frecuencia real de cada entrypoint, número de relecturas, configuración efectiva de firma/allowlist, estado de procesos, volúmenes y coste de ciclos repetidos.

**Por validar:** qué entrypoint es el único autorizado en cada entorno; si se pretende permitir replay manual; requisitos de retención/deduplicación; compatibilidad con consumidores fuera de este repositorio; y cómo versionar el envelope sin invalidar snapshots existentes.

## 8. Referencias externas de ingeniería (Exa)

- OpenTelemetry, [Context propagation](https://opentelemetry.io/docs/concepts/context-propagation/): Trace ID y Span ID correlacionan operaciones a través de límites de proceso; la documentación advierte validar/sanitizar contexto recibido de fuentes no confiables.
- W3C, [Trace Context](https://www.w3.org/TR/trace-context/): estándar para propagar contexto mediante `traceparent`/`tracestate`.
- JSON Schema, [Object / Required Properties](https://json-schema.org/understanding-json-schema/reference/object): los campos no son obligatorios por defecto; la obligación debe declararse explícitamente.
- JSON Schema, [Type-specific Keywords / Format](https://json-schema.org/understanding-json-schema/reference/type): `format: date-time` es una anotación salvo que el validador active la aserción; la semántica temporal debe validarse también en la implementación.
- Microsoft Azure Architecture Center, [Idempotent Consumer](https://learn.microsoft.com/en-us/azure/architecture/patterns/idempotent-consumer): la deduplicación requiere un identificador estable de mensaje, persistencia durable y atomicidad/concurrencia; no debe usarse un correlation ID como clave idempotente.

## 9. Decisión de esta revisión

**No se modificó código funcional, pruebas, configuración ni infraestructura.** La revisión de consumidores refina los hallazgos anteriores: RSX-02 no evidencia un bypass en los entrypoints actuales, y RSX-01 afecta principalmente a la API genérica del writer, no al fetcher canónico Binance.

**Siguiente acción única:** definir y aprobar el contrato versionado de observación RSX (schema_version + observation_id + procedencia + timestamps + estado de verificación) y su política de replay antes de tocar el código.