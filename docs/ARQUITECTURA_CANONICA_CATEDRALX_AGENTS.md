# Referencia canónica de integración: CatedralX ↔ Agents

> **Estado:** lectura estática de repositorios; no certifica runtime ni producción. Fecha: 2026-11-23.  
> **Alcance:** documentación solamente. No se modificó lógica funcional ni se ejecutaron tests, CI o despliegues.

## 1. Identidad y alcance

CatedralX es actualmente un motor experimental de razonamiento y análisis financiero. Valida observaciones, calcula métricas y produce resultados estructurados con evidencia dentro de ese dominio. No debe describirse como motor universal de inteligencia empresarial ni como sistema de trading de producción. Las etiquetas `buy`, `sell`, `hold` son analíticas: no crean órdenes ni autorizan ejecución.

Agents coordina la admisión, persistencia, invocación, candidate store, verificación independiente y distribución condicionada.

## 2. Responsabilidades

| Responsabilidad | Componente |
|---|---|
| Evaluación financiera y `DecisionResult` | CatedralX |
| API, autenticación, permisos y contrato de solicitud | Agents API |
| Persistencia/coordinación de tareas | Agents TaskBus |
| Invocación de CLI y transporte de entradas/salidas | Agents worker |
| Persistencia del candidato | Candidate Store |
| Verificación independiente | Agents verifier |
| Registro de aceptación/distribución | Agents stores/API |
| Producción de métricas empresariales de gobernanza | Productor upstream aún no identificado |

La Membrana es un patrón de controles distribuido entre estos componentes, no un microservicio independiente.

## 3. Contrato de gobernanza: dos objetos separados

### `central_dimensions_bp`

Cinco puntuaciones explícitas, enteras entre 0 y 10000:
- `viability_bp`
- `human_value_bp`
- `distribution_bp`
- `resilience_bp`
- `evidence_bp`

CatedralX consume `viability_bp` como entrada explícita. No se debe afirmar que lo deriva automáticamente de `buy`, `sell` o `hold`.

### `dynamic_constraints`

Métricas dinámicas como:
- `reinvestment_surplus`
- `entropy_rate`
- `entropy_time_scale`
- `loop_gain`
- `signal_count`, `optimal_signal_count`
- `exposure`, `max_exposure`
- `resilience`, `minimum_resilience`

`reinvestment_surplus` pertenece a `dynamic_constraints`, no a `central_dimensions_bp`. CatedralX evalúa restricciones dinámicas; Agents transporta las entradas y no las calcula.

## 4. Regla multicriterio

`elite/REASON/multicriteria.py` define:
- Score: `(3500 * viability_bp + 2500 * resilience_bp + 2000 * human_value_bp + 2000 * distribution_bp) / 10000`.
- Umbral del score: 7000 puntos básicos.
- Gate de evidencia: 8500 puntos básicos.
- Gate de reinversión: entrada Decimal válida y reglas de déficit del evaluador.

Los gates duros prevalecen sobre el score. El hash de evaluación cubre la política y el veredicto canónico, no los precios de entrada; no usarlo como sustituto de procedencia de datos de origen.

## 5. Procedencia y frontera de confianza

La atestación criptográfica de la observación de mercado no acredita el origen de las cinco puntuaciones de gobernanza. La validación de estructura/rango no prueba fuente, método, periodo/grano, frescura ni calidad semántica.

El contrato de Agents inspeccionado no impone un sobre de procedencia por puntuación. Se requiere un contrato versionado con propietario, fuente, grano, fórmula/versión, timestamp, frescura, unidad/escala, referencia de evidencia y digest verificable.

## 6. Rutas diferenciadas

1. `catedralx_reasoning`: herramienta de razonamiento/análisis; no equivale a evaluación económica gobernada.
2. `catedralx_economic_evaluation`: `POST /v1/request` → TaskBus → worker → snapshot → CatedralX → `DecisionResult`.
3. `catedralx_opportunity_evaluation`: evaluación de oportunidades vía CLI `BIN/catedral economic-opportunity`.
4. `catedralx_economic_proposal_review`: ruta reservada al ingreso autenticado desde CatedralX.

No intercambiar payloads ni garantías entre estas rutas.

## 7. Estados, identificadores y autoridad

- `trace_id` / `traceparent`: correlación de ejecución.
- `evaluation_hash`: identidad/integridad del resultado de evaluación.
- `candidate_id`: candidato en Agents.
- `decision_id`: identificador usado por el contrato de aceptación de Agents.
- `execution_id`: ejecución/despacho si ocurre.

No usar `acceptance_id` como clave canónica de aceptación: el contrato inspeccionado utiliza `decision_id`.

HMAC-SHA256 de Candidate Store y Ed25519 de aceptación tienen propósitos distintos. La validez criptográfica no demuestra corrección semántica ni conveniencia económica.

Una evaluación `ACCEPTED` de CatedralX no equivale a aceptación independiente en Agents. Autorización humana, aceptación independiente, despacho y ejecución son etapas distintas.

## 8. Evidencia estática y brechas

| Elemento | Evidencia localizada | Conclusión permitida |
|---|---|---|
| Pipeline CatedralX | `elite/`, CLI y grafo | Relaciones estáticas identificadas |
| `DecisionResult` | Contratos y result store | Contrato presente |
| Invocación desde Agents | `api/worker_loop.py` y adaptador | Ruta presente en código |
| `central_dimensions_bp` | Validación, transporte, consumo y fixtures | Productor conectado no localizado |
| `dynamic_constraints` | Evaluador en CatedralX y transporte en Agents | Productor upstream real no demostrado |
| Procedencia de puntuaciones | No exigida por contrato estructural actual | Requiere contrato versionado |
| E2E con datos reales | No ejecutada en esta revisión | No demostrada |
| Runtime/producción | No inspeccionado | No demostrado |

## 9. Próximos criterios de cierre

1. Identificar productor y propietario de las cinco puntuaciones.
2. Identificar productor y fuentes de las métricas dinámicas.
3. Definir procedencia/frescura por campo y contrato versionado.
4. Ejecutar E2E reproducible API → TaskBus → worker → CatedralX → `DecisionResult`.
5. Verificar aceptación independiente con `decision_id`, firma, autorización y distribución condicionada.

Esta revisión fue estática; no ejecutó código, tests, CI, contenedores ni servicios, ni inspeccionó secretos, bases de datos operativas o telemetría.

## 10. Fuentes

- [README de CatedralX](../README.md)
- [Grafo de dependencias](./GRAFO_DEPENDENCIAS_VERIFICADO.md)
- [Cálculo multicriterio](./REASON/multicriteria.py)
- [Percepción y validación](./PERCEIVE/percepcion.py)
- [Agents task_contracts.py](https://github.com/Chalamandra-Magistral-deco/chalamandra-agent-engine/blob/main/api/task_contracts.py)
- [Agents worker_loop.py](https://github.com/Chalamandra-Magistral-deco/chalamandra-agent-engine/blob/main/api/worker_loop.py)
