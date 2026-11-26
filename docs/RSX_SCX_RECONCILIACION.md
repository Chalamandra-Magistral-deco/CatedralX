# Reconciliación RSX–SCX: percepción, contrato y entrada al razonamiento

> **Estado:** auditoría estática de la rama `docs/canonical-architecture-20261123`. Se inspeccionaron archivos versionados y pruebas; no se ejecutó el sistema ni CI. Este documento registra hallazgos y correcciones propuestas. No cambia comportamiento.

## 1. Alcance y fuentes inspeccionadas

Código:
- `elite/PERCEIVE/stream_altar.py`
- `elite/PERCEIVE/sensors.py`
- `elite/PERCEIVE/data_feeder.py`
- `elite/PERCEIVE/snapshot_signing.py`
- `elite/PERCEIVE/api_pulse.py`
- `elite/PERCEIVE/percepcion.py`
- `elite/PERCEIVE/bunker.py`
- `elite/REASON/schemas.py`
- `elite/REASON/razon.py`
- `elite/REASON/orchestrator.py`

Pruebas/documentación:
- `tests/test_acceptance_contract.py`
- `tests/test_snapshot_freshness.py`
- `tests/test_trace_propagation.py`
- `docs/MAPA_SAGRADO.md`
- `docs/CONTRATO_ARQUITECTONICO.md`
- `docs/GRAFO_DEPENDENCIAS_VERIFICADO.md`

La inspección es estática sobre el contenido de GitHub de la rama indicada. No demuestra runtime, CI reciente, configuración de secretos, conexión al proveedor ni actividad de Bunker.

## 2. Flujo observado

```text
Proveedor / caller
    |
    v
stream_altar.run_once / accept_observation
    |
    v
sensors.normalize_market_payload
    |
    v
data_feeder.write_observation
    |  envelope PERCEIVE + HMAC cuando firma requerida
    v
snapshot JSON
    |
    +--> REASON.razon.main
    |       api_pulse.validate_snapshot_payload
    |       percepcion.from_snapshot
    |       SensoryInput
    |       trace_id
    |       orchestrator.execute_cycle
    |       DecisionResult + result store
    |
    +--> PERCEIVE.bunker.BunkerDaemon
            api_pulse.validate_snapshot_payload
            percepcion.from_snapshot
            SensoryInput
            orchestrator.execute_cycle
            resultado resumido en memoria/log
```

El grafo es una representación de rutas estáticas identificadas; no significa que ambas entradas estén activas simultáneamente.

## 3. Hechos observados

### RSX — adquisición y normalización

1. `stream_altar.build_observation_from_klines` acepta velas cerradas de un minuto, comprueba orden, unicidad, continuidad, precios positivos y finitos, mínimo de 30 velas y antigüedad máxima de 120 segundos. Construye `source` y `observed_at`.
2. `stream_altar.run_once` y `accept_observation` delegan la escritura al writer; no añaden por sí mismos un identificador de evento o una clave de idempotencia.
3. `sensors.normalize_market_payload` valida historial, precio, gap/inercia, source y el tipo de `observed_at` si está presente. Sin embargo, permite que `observed_at` esté ausente y asigna `source="unspecified"` si falta.
4. `data_feeder.write_observation` normaliza, envuelve el resultado bajo `PERCEIVE`, firma si la configuración exige firma y escribe mediante archivo temporal, fsync y replace atómico.
5. La firma de snapshot es HMAC-SHA256 sobre el JSON canónico de la sección `PERCEIVE`. No es una firma asimétrica ni prueba que el proveedor haya sido honesto; la allowlist de source y la clave son parte del límite de confianza.

### Validación del snapshot

6. `api_pulse.validate_snapshot_payload` exige objeto raíz, sección `PERCEIVE`, al menos 30 precios positivos y finitos, precio actual igual al último histórico, timestamp ISO-8601 con zona horaria, frescura (por defecto 120 s), tolerancia de reloj futuro de 5 s y gap/inercia dentro de [-1, 1].
7. Con firma requerida, valida source contra allowlist y verifica HMAC. Con firma no requerida, el resultado declara `signature="not_required"`; esta ruta debe mantenerse limitada a pruebas aisladas.
8. `percepcion.from_snapshot` valida forma de los campos de gobernanza y normaliza la sección `PERCEIVE` a `SensoryInput`. No ejecuta por sí misma la verificación de firma ni frescura; esa responsabilidad está en los entrypoints inspeccionados.
9. `SensoryInput` contiene precios, gap, inercia, free_energy_prev y campos de gobernanza. No transporta explícitamente `source`, `observed_at`, identificador de observación ni hash del snapshot al contrato tipado de SCX.

### SCX — razonamiento y trazabilidad

10. `REASON.razon.main` comprueba el marcador de pánico, lee el snapshot, valida con `validate_snapshot_payload`, convierte mediante `from_snapshot`, obtiene `CATEDRALX_TRACE_ID` o genera UUID hexadecimal y llama a `execute_cycle`.
11. La ruta one-shot incluye `trace_id` en el resultado y en `DecisionResult`, y persiste el resultado mediante `append_result`.
12. `orchestrator.execute_cycle` valida o genera un trace ID W3C de 32 caracteres hexadecimales, propaga la traza a `think` y a la procedencia RSX/SCX/DSX. Las pruebas existentes verifican traza explícita, generación y rechazo de IDs inválidos.
13. `PERCEIVE.bunker.BunkerDaemon` realiza validación y conversión equivalentes, pero llama a `execute_cycle(sensory)` sin pasar explícitamente `trace_id`. El orquestador genera uno nuevo para ese ciclo. Bunker agrega un resumen REASON al objeto snapshot en memoria y escribe logs, pero el código inspeccionado no persiste ese objeto modificado ni usa el mismo flujo one-shot de `DecisionResult`.
14. Las pruebas inspeccionadas verifican rechazo de snapshots caducados en ambos entrypoints y propagación de traza en el orquestador. No se identificó en el conjunto revisado una prueba que exija paridad de trazabilidad y contrato de salida entre `razon.main` y Bunker.

## 4. Discrepancias y correcciones propuestas

| ID | Severidad | Hecho | Riesgo | Corrección propuesta |
|---|---|---|---|---|
| RSX-01 | Alta | Normalizador permite `observed_at=None` y `source="unspecified"`; validador posterior los rechaza en el flujo firmado/canónico | El productor puede escribir y firmar un snapshot que el consumidor no puede aceptar | Hacer obligatorios `observed_at` con zona horaria y `source` permitido en el contrato de producción del writer; conservar bypass sintético solo en fixtures aislados |
| RSX-02 | Alta | `from_snapshot` confía en que el caller ya validó firma/frescura | Un consumidor nuevo puede invocar conversión y razonamiento saltándose la validación del snapshot | Consolidar una única función pública de entrada validada o hacer explícito un tipo/objeto validado no construible desde payload crudo; mantener validación en todos los entrypoints |
| RSX-03 | Media | `SensoryInput` pierde source, observed_at e identidad/hash de observación | SCX y MSX no reciben directamente la procedencia original a través del contrato tipado | Extender el contrato con metadatos de observación inmutables (source, observed_at, observation_id/snapshot_hash y versión del contrato) o enlazar un registro RSX inmutable por ID |
| SCX-01 | Media | Bunker no pasa trace_id upstream; genera uno nuevo y no devuelve/persiste DecisionResult como el one-shot | Trazabilidad y evidencia de salida distintas según entrypoint | Definir política única: aceptar contexto trace entrante validado o generar uno; ambos entrypoints deben emitir el mismo contrato mínimo de ciclo y evidencia, sin mutar snapshot original |
| SCX-02 | Media | No se observa clave de idempotencia/event_id en el writer/entrypoints del snapshot | Relectura o reintento puede repetir el ciclo y consumir presupuesto/registrar nuevas salidas | Definir `observation_id` estable y política explícita de replay; deduplicación durable y atómica para efectos persistentes antes de prometer idempotencia |
| SCX-03 | Baja | `api_pulse` devuelve un dict de estado, mientras `from_snapshot` recibe dict crudo | La frontera entre payload sin validar y payload validado depende de disciplina del caller | Introducir contrato tipado `ValidatedSnapshot` o equivalente, manteniendo compatibilidad controlada y pruebas negativas |

### Orden recomendado

1. **RSX-01 primero:** impedir que el writer canónico persista snapshots estructuralmente incompletos que el lector rechazará.
2. **RSX-02 y RSX-03:** sellar la frontera de confianza y conservar procedencia hasta SCX/MSX.
3. **SCX-01:** unificar traza y evidencia de salida entre one-shot y Bunker.
4. **SCX-02:** definir replay/idempotencia sin usar `trace_id` como clave de deduplicación. Una traza correlaciona; no identifica necesariamente una operación lógica única.

## 5. Contrato mínimo propuesto RSX → SCX

El contrato lógico recomendado para la frontera es:

- `observation_id`: identidad estable de la observación, no derivada del intento de entrega.
- `source`: proveedor/fuente permitido y explícito.
- `observed_at`: timestamp ISO-8601 con zona horaria.
- `received_at`: instante de recepción local, distinto del tiempo observado.
- `snapshot_hash`: hash del envelope canónico verificado, además del estado de firma.
- `schema_version`: versión explícita del contrato de entrada.
- `payload`: precios y features normalizados con unidades/semántica documentadas.
- `trace_id`: contexto de correlación de la ejecución, separado de `observation_id`.
- `validation_status`: solo un estado validado puede cruzar a razonamiento.
- `validation_evidence`: versión del validador, política de frescura y resultado de firma/procedencia.

Los campos anteriores son propuesta de contrato; no se afirma que todos existan hoy.

## 6. Pruebas que deben añadirse antes de cerrar la frontera

1. Writer rechaza timestamp ausente, timestamp sin zona horaria y source fuera de allowlist en modo producción.
2. Writer → lector: todo snapshot escrito por el productor canónico pasa validación si no ha expirado y no fue alterado.
3. Firma ausente, firma incorrecta, clave desconocida, source no permitido, precio NaN/Infinity, booleano, historia insuficiente, timestamp obsoleto y timestamp futuro: todos bloquean antes de llamar a SCX.
4. Llamar a conversión/entrada pública con payload crudo o no validado no permite alcanzar `execute_cycle`.
5. Procedencia source/time/hash/observation_id permanece asociada al resultado y a los registros MSX.
6. One-shot y Bunker propagan un trace ID válido y producen un contrato de salida consistente; los spans hijos conservan relación causal.
7. Replay del mismo `observation_id` no duplica consumo de presupuesto ni resultados persistidos; concurrencia y crash-window se prueban con almacenamiento durable.
8. Cambio de schema_version o política de frescura exige pruebas de compatibilidad y revisión de consumidores.

No se deben prometer “exactly once” en un sistema distribuido. La meta verificable es procesamiento efectivamente único mediante identidad estable, deduplicación durable, atomicidad donde sea posible y reconciliación de efectos externos.

## 7. Hipótesis y datos ausentes

- **Hipótesis:** el camino Bunker se utiliza como alternativa de ciclo continuo. No se afirma que esté desplegado o activo.
- **Hipótesis:** el flujo de snapshot es el único contrato RSX→SCX para todas las modalidades. La inspección se centró en el camino de observación de mercado y no prueba todos los adaptadores.
- **Ausente:** telemetría de runtime, conteos, latencias, fallos y volumen de snapshots.
- **Ausente:** configuración efectiva de claves HMAC, allowlist, variables de entorno y ruta de snapshot en una instalación.
- **Ausente:** ejecución CI del SHA de esta rama para los archivos revisados.
- **Ausente:** evidencia de conexión real a Binance o de ejecución reciente del proveedor.
- **Ausente:** integración runtime con Agents; queda fuera de este tramo RSX–SCX.

## 8. Fuentes técnicas externas

- OpenTelemetry, [Context propagation](https://opentelemetry.io/docs/concepts/context-propagation/): el contexto de traza correlaciona operaciones a través de procesos; Trace ID y Span ID tienen funciones diferentes. La propagación debe validarse y tratarse con cautela cuando el emisor es externo.
- W3C Trace Context, [Recommendation](https://www.w3.org/TR/trace-context/): formato y reglas interoperables para `traceparent` y `tracestate`.
- Microsoft Azure Architecture Center, [Idempotent Consumer](https://learn.microsoft.com/en-us/azure/architecture/patterns/idempotent-consumer): usar identidad estable de mensaje, deduplicación durable y atomicidad; no confundir correlation ID con clave idempotente.
- Li et al., [Refining Perception Contracts](https://arxiv.org/abs/2311.08652): los contratos de percepción deben relacionar condiciones de entrada, incertidumbre y requisitos verificables del sistema consumidor.

## 9. Decisión de esta revisión

**No se modificó código funcional.** La evidencia estática es suficiente para identificar discrepancias y proponer un orden de corrección, pero no para decidir detalles de compatibilidad, migración de snapshots o semántica de replay sin revisar todos los consumidores y sus pruebas.

**Siguiente acción única:** revisar todos los consumidores de `write_observation`, `from_snapshot` y `SensoryInput` (incluidos tests y adaptadores) para cerrar el impacto de RSX-01/02/03 antes de cambiar el contrato.