# Referencia canónica de integración: CatedralX ↔ Agents

> **Estado:** documentación de arquitectura contrastada mediante lectura estática de GitHub. No certifica runtime, despliegue ni producción.  
> **Fecha:** 2026-11-23.  
> **HEAD inspeccionado:** `main` (snapshot de referencia de esta revisión).  
> **Alcance del cambio:** documentación únicamente; no se modificó lógica funcional.

## 1. Identidad y alcance de CatedralX

CatedralX es, en su implementación documentada actual, un motor experimental de razonamiento y análisis financiero. Transforma observaciones de mercado y contexto computable en resultados estructurados, reproducibles y verificables.

Su README establece límites explícitos:
- valida series cronológicas y calcula métricas financieras;
- clasifica escenarios mediante reglas deterministas con etiquetas analíticas `buy`, `sell` o `hold`;
- aplica condiciones de protección;
- conserva estado, resultados y evidencia de evaluación;
- no crea precios sintéticos para completar datos ausentes;
- no crea ni ejecuta órdenes;
- no está validado como sistema de trading de producción.

Por tanto, no presentar la implementación actual como motor universal de inteligencia empresarial, agente autónomo de ejecución ni sistema listo para operar capital real.

## 2. Responsabilidad en el ecosistema

CatedralX es responsable de su razonamiento y de la producción de su resultado canónico. Agents es responsable de la coordinación operacional que lo invoca y transporta.

| Responsabilidad | Dueño |
|---|---|
| Interpretación analítica dentro del dominio de CatedralX | CatedralX |
| Construcción y validación del contrato `DecisionResult` | CatedralX |
| Persistencia canónica de resultados y evidencia propia | CatedralX |
| Admisión HTTP, autenticación y contrato de solicitud | Agents API |
| Persistencia y coordinación de tareas | Agents TaskBus |
| Invocación del CLI y adaptación de la respuesta | Agents worker |
| Persistencia del candidato operacional | Agents Candidate Store |
| Verificación independiente del candidato | Agents verifier |
| Registro de aceptación y distribución condicionada | Agents stores/API |
| Producción de dimensiones empresariales de gobernanza | Producto/analytics propietario; no Agents |

La frontera contractual se implementa mediante controles distribuidos en API, contratos, TaskBus, worker, stores y verificador. No se presupone un microservicio separado llamado Membrana.

## 3. Rutas de integración que deben permanecer diferenciadas

Agents documenta más de una ruta relacionada con CatedralX. No son intercambiables:

1. `catedralx_reasoning`: herramienta de análisis de precios disponible para enrutamiento especializado; no es la evaluación económica gobernada.
2. `catedralx_economic_evaluation`: solicitud explícita a través de `POST /v1/request`, TaskBus y worker, que invoca el adaptador canónico de CatedralX.
3. `catedralx_opportunity_evaluation`: evaluación de oportunidad mediante CLI `BIN/catedral economic-opportunity`.
4. `catedralx_economic_proposal_review`: ruta reservada al ingreso autenticado desde CatedralX.

Cada ruta debe mantener su propio esquema, autenticación, procedencia, semántica de estados y criterios de aceptación.

## 4. Contrato de resultado y trazabilidad

`DecisionResult` es el resultado estructurado de CatedralX. No debe confundirse con el candidato de Agents ni con el registro de aceptación independiente.

Distinguir:
- `trace_id`: correlación de la ejecución.
- `catedralx_trace_id`: correlación específica de CatedralX, cuando el contrato de esa ruta lo incluya.
- `evaluation_hash`: referencia de integridad/identidad de la evaluación.
- `candidate_id`: identidad del candidato operacional en Agents.
- `acceptance_id`: identidad del registro de aceptación.
- `execution_id`: identidad de una ejecución/despacho, si ocurre.

La presencia de estos campos en código o pruebas no demuestra propagación universal. Cada ruta requiere pruebas de contrato y trazabilidad específicas.

## 5. Autoridad, seguridad y estados

- CatedralX produce evaluación y evidencia; no otorga por sí mismo autorización externa.
- Agents coordina y ejecuta solo las acciones admitidas por contratos y permisos aplicables.
- HMAC-SHA256 de Candidate Store y firma Ed25519 del mecanismo de aceptación tienen propósitos distintos.
- La validez criptográfica no demuestra corrección semántica ni rentabilidad.
- `DecisionResult.status = ACCEPTED` no equivale a aceptación independiente del candidato en Agents.
- La autorización humana, la aceptación independiente, el despacho y la ejecución son etapas distintas.
- Un resultado rechazado, incierto o incompleto debe permanecer fail-closed.

## 6. Correspondencia estática y límites de evidencia

| Elemento | Evidencia localizada | Conclusión permitida |
|---|---|---|
| Pipeline cognitivo | Grafo de dependencias en `docs/GRAFO_DEPENDENCIAS_VERIFICADO.md` | Relaciones estáticas identificadas |
| `DecisionResult` | `elite/contracts/builder.py`, result store y README | Contrato presente en el repositorio |
| Persistencia de resultados | `elite/contracts/result_store.py` y rutas documentadas | Escritura/lectura implementada en código |
| Evaluación/gobernanza económica | `elite/FEX/GOVERNANCE/economic_cycle.py` y CLI asociada | Flujo y ledger localizables |
| Despacho hacia Agents | `elite/bin/dispatch_agents.py` y scanner asociado | Adaptador de salida localizado; tests con HTTP simulado no prueban servicio remoto |
| Invocación desde Agents | Agents `api/worker_loop.py` y adaptador canónico | Ruta de invocación presente en código de Agents |
| Integración E2E vigente | No ejecutada durante esta revisión | No demostrada |
| Runtime/producción | No inspeccionado | No demostrado |

El grafo de dependencias es un inventario estático. Distingue importación, invocación, lectura/escritura, protección por pruebas y actividad en runtime; no inferir runtime a partir del código o de tests aislados.

## 7. Brechas compartidas

1. **Productor de gobernanza:** falta demostrar el productor de producto/analytics que genera `central_dimensions_bp` con datos reales, frescura y procedencia.
2. **E2E con gobernanza real:** falta una ejecución vigente y reproducible con esas entradas.
3. **Trazabilidad extremo a extremo:** verificar por cada ruta la conservación de `trace_id`, `traceparent`, `evaluation_hash` y referencias específicas.
4. **Estados canónicos:** separar evaluación CatedralX, autorización, candidato, aceptación independiente, despacho y ejecución.
5. **Pruebas de distribución:** verificar que no se entrega un candidato sin aceptación y permisos válidos.
6. **Evidencia de operación:** aportar entorno, commit, fecha, configuración no secreta, trazas y resultado observable antes de afirmar producción.

## 8. Criterios de madurez

No colapsar estas categorías:
1. **Existe:** artefacto localizado.
2. **Invocado:** llamada estática identificada.
3. **Protegido:** prueba localizada.
4. **Integrado:** prueba entre componentes ejecutada y registrada.
5. **Operativo:** runtime observado con evidencia reproducible.
6. **Aceptado:** verificación independiente y registro de aceptación.

Esta revisión no ejecutó código, tests, CI, contenedores ni servicios. Tampoco inspeccionó claves, secretos, bases de datos operativas o telemetría de producción.

## 9. Fuentes y documento coordinador

- [README de CatedralX](../README.md)
- [Grafo de dependencias de CatedralX](./GRAFO_DEPENDENCIAS_VERIFICADO.md)
- [README de Agents](https://github.com/Chalamandra-Magistral-deco/chalamandra-agent-engine/blob/main/README.md)
- [Integración de gobernanza en Agents](https://github.com/Chalamandra-Magistral-deco/chalamandra-agent-engine/blob/docs/canonical-architecture-20261123/docs/INTEGRACION_GOVERNANCE.md)
- [Especificación canónica compartida en Agents](https://github.com/Chalamandra-Magistral-deco/chalamandra-agent-engine/blob/docs/canonical-architecture-20261123/docs/ARQUITECTURA_CANONICA_CATEDRALX_AGENTS.md)

## 10. Regla de cambio

OBSERVAR → INTERPRETAR → RECOMENDAR → AUTORIZAR → EJECUTAR → VERIFICAR → DOCUMENTAR.

Esta referencia no autoriza cambios de lógica, contratos funcionales, secretos, despliegues ni operaciones externas. Las modificaciones funcionales requieren autorización específica.
