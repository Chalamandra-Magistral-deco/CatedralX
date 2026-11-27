# Contrato DecisionResult ↔ Candidate ↔ Acceptance

**Estado:** documentación de contrato observada en `main`; no implica despliegue E2E ni autorización de ejecución.
**Versión del documento:** 1.0.0
**Fecha de inspección:** 2026-11-26
**Repositorio propietario de este documento:** `Chalamandra-Magistral-deco/CatedralX`
**Alcance:** describir el contrato que existe en CatedralX y Agents, señalar las uniones verificables y separar los requisitos pendientes de los comportamientos ya implementados.

## 1. Principios normativos

1. Un `DecisionResult` es un resultado analítico de CatedralX. No es una aceptación independiente, una orden ni una ejecución.
2. Un `Candidate` es un objeto persistido y verificable en Agents. Su existencia no significa que haya sido aceptado.
3. Una `Acceptance` es una decisión independiente, firmada por el proceso verificador de Agents. No debe inferirse a partir del estado de CatedralX.
4. La firma Ed25519 autentica el payload firmado; no demuestra por sí sola que el razonamiento, la evidencia o la decisión sean correctos.
5. Los controles deben fallar de forma cerrada: ausencia, inconsistencia o invalidez de evidencia, identidad, digest o firma impide aceptar o distribuir.
6. La documentación no declara que el flujo completo esté probado en runtime o desplegado en producción.

## 2. DecisionResult — contrato actual de CatedralX

Fuente ejecutable inspeccionada: [elite/contracts/schemas/decision_result.json](../elite/contracts/schemas/decision_result.json).

El schema declara JSON Schema Draft 2020-12 y exige estos campos:

| Campo | Regla observada |
|---|---|
| `result_id` | string |
| `status` | `ACCEPTED`, `UNCERTAIN`, `REJECTED` o `BLOCKED_MISSING_INPUT` |
| `engine` | constante `CatedralX` |
| `decision` | string |
| `evidence` | array de objetos |
| `assumptions` | array de strings |
| `risks` | array de strings |
| `provenance` | array de strings |
| `trace_id` | 32 caracteres hexadecimales minúsculos |
| `analysis_only` | boolean constante `true` |
| `orders_created` | boolean constante `false` |
| `orders_executed` | boolean constante `false` |
| `evaluation_hash` | 64 caracteres hexadecimales minúsculos |
| `evaluation_gate` | `ACCEPTED`, `REJECTED`, `BLOCKED_EVIDENCE`, `BLOCKED_REINVERSION`, `BLOCKED_UNCERTAINTY` o `BLOCKED_DEFICIT` |
| `cycle_id` | string, integer o null |

El schema también define `tests`, `next_action`, `missing_inputs`, `blocking_reasons` y `evaluation_reason` como propiedades opcionales. Cuando `status=ACCEPTED`, exige al menos un elemento en `evidence` y `provenance`.

### 2.1 Interpretación y límites

- `status=ACCEPTED` es un estado del resultado analítico de CatedralX. **No equivale** a `outcome=accepted` en Agents.
- `evaluation_gate` es una compuerta de evaluación de CatedralX; no sustituye la aceptación independiente.
- `evaluation_hash` es obligatorio en el schema actual. No se admite `null`. Cualquier cambio a opcional/null requiere una modificación coordinada del schema, productores y consumidores, más pruebas de compatibilidad.
- El patrón actual de `trace_id` exige 32 caracteres hexadecimales minúsculos, pero el schema no excluye explícitamente el valor de todos ceros. Agents sí lo rechaza en Acceptance y valida que coincida con el candidato. Esta diferencia queda registrada como discrepancia de validación, no se corrige silenciosamente aquí.
- El schema no declara `additionalProperties: false`; por tanto, no debe afirmarse que el schema rechaza propiedades adicionales.
- `result_id`, `cycle_id` y `evaluation_hash` no son intercambiables con `candidate_id`, `decision_id` ni `evidence_digest`.

## 3. Candidate — frontera de persistencia en Agents

El Candidate es persistido por Agents y posee su propio identificador. La inspección de `api/candidate_store.py` encontró:

- integridad del registro del candidato mediante HMAC-SHA256;
- digest de evidencia calculado mediante SHA-256;
- persistencia append-only JSONL e índice;
- escritura idempotente para el mismo `candidate_id` y contenido idéntico; conflicto si el mismo identificador se reutiliza con contenido distinto.

El HMAC del candidato y la firma Ed25519 de Acceptance tienen finalidades distintas. No deben compartir nombre, semántica ni sustitución criptográfica.

**Relación que debe conservar la integración:** el candidato transporta el `trace_id` y la evidencia que serán comprobados por Acceptance. El almacén de Acceptance vuelve a calcular el digest de evidencia del candidato y exige igualdad exacta.

## 4. Acceptance — contrato actual de Agents

Fuentes ejecutables inspeccionadas:

- [api/crypto_signer.py](https://github.com/Chalamandra-Magistral-deco/chalamandra-agent-engine/blob/main/api/crypto_signer.py)
- [verifier/independent_acceptance_verifier.py](https://github.com/Chalamandra-Magistral-deco/chalamandra-agent-engine/blob/main/verifier/independent_acceptance_verifier.py)
- [api/acceptance_store.py](https://github.com/Chalamandra-Magistral-deco/chalamandra-agent-engine/blob/main/api/acceptance_store.py)

### 4.1 Payload firmado

El objeto de decisión contiene exactamente estos diez campos canónicos:

| Campo | Tipo/regla observada |
|---|---|
| `decision_id` | string no vacío |
| `candidate_id` | string no vacío |
| `outcome` | `accepted` o `rejected` |
| `criteria_checked` | array de strings |
| `reasons` | array de strings |
| `missing_evidence` | array de strings |
| `verifier_id` | string no vacío; debe coincidir con la identidad configurada |
| `evidence_digest` | SHA-256 hexadecimal de 64 caracteres minúsculos |
| `decided_at` | fecha ISO-8601 con zona horaria |
| `trace_id` | 32 caracteres hexadecimales minúsculos, no todos ceros |

Reglas semánticas implementadas por el verificador:

- Rechaza campos canónicos ausentes y propiedades adicionales en el objeto de decisión que recibe para firmar.
- Para `accepted`, `criteria_checked` no puede estar vacío y `reasons` y `missing_evidence` deben estar vacíos.
- Para `rejected`, debe existir al menos un motivo o evidencia faltante.
- La confirmación operativa debe coincidir exactamente con `ACCEPT:<candidate_id>` o `REJECT:<candidate_id>`, según el outcome.
- La firma es Ed25519. La semilla privada se lee exclusivamente en el proceso independiente del verificador; el módulo API contiene verificación con clave pública, no función de firma.

### 4.2 Serialización y firma: descripción exacta de la implementación

`api/crypto_signer.py:create_canonical_payload` selecciona los diez campos anteriores, construye un objeto con esos campos y serializa mediante:

- `json.dumps(..., sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)`;
- codificación UTF-8;
- firma/verificación Ed25519 sobre esos bytes.

**Precisión criptográfica:** esta es la canonicalización implementada por el repositorio. No se declara compatible con RFC 8785 (JCS). Ordenar claves y eliminar espacios no basta para afirmar conformidad completa con JCS, que también define reglas de serialización de números, cadenas y orden de propiedades. No cambiar el algoritmo de canonicalización sin una migración coordinada, vectores de prueba y compatibilidad entre firmante y verificador.

La propiedad `signature` acompaña al payload firmado, pero no forma parte de los diez campos firmados. La API verifica la firma usando `CHALAMANDRA_VERIFIER_PUBLIC_KEY`; el proceso de verificación firma con `CHALAMANDRA_ED25519_SEED` y la identidad `CHALAMANDRA_VERIFIER_ID`.

### 4.3 Persistencia y controles del Acceptance Store

El almacén `acceptance_store.jsonl`:

1. exige los diez campos canónicos y la firma;
2. comprueba la identidad del verificador configurada;
3. verifica la firma Ed25519;
4. recupera el candidato y exige que el `trace_id` coincida;
5. recalcula el digest de evidencia del candidato y exige coincidencia;
6. para `outcome=accepted`, exige que el candidato tenga estado `candidate`;
7. trata como idempotente una repetición idéntica de `decision_id`, pero rechaza el mismo ID con contenido diferente;
8. impide registrar una segunda decisión para el mismo candidato; una nueva revisión requiere un nuevo candidato.

La distribución no debe tratar un Candidate como publicable: la condición de aceptación independiente es el resultado verificable de Acceptance.

## 5. Identificadores y correlación

| Identificador | Propietario/uso | No debe confundirse con |
|---|---|---|
| `result_id` | Resultado emitido por CatedralX | `candidate_id`, `decision_id` |
| `cycle_id` | Ciclo de análisis de CatedralX | `trace_id` |
| `trace_id` | Correlación distribuida; 16 bytes expresados como 32 hex | `cycle_id`, `result_id` |
| `evaluation_hash` | Huella de evaluación de CatedralX | `evidence_digest` |
| `candidate_id` | Identidad del candidato persistido por Agents | `result_id`, `decision_id` |
| `decision_id` | Identidad de la decisión independiente de Acceptance | `candidate_id`, `result_id` |
| `evidence_digest` | SHA-256 de evidencia del candidato | `evaluation_hash` |

W3C Trace Context define `trace-id` como 16 bytes representados por 32 caracteres hexadecimales en minúsculas y prohíbe el valor de todos ceros. El campo local `trace_id` corresponde a ese identificador; no es el header completo `traceparent` (que también incluye versión, parent-id y flags).

**Unión pendiente de formalización:** los fragmentos inspeccionados verifican el `trace_id` entre candidato y Acceptance, pero no establecen por sí solos una referencia obligatoria `result_id → candidate_id` dentro de los diez campos firmados. No inventar esa relación como si ya estuviera implementada. Antes de exigirla, definir el campo de enlace en el contrato de Candidate o en el sobre de transporte, y cubrirlo con pruebas.

## 6. Máquina de estados mínima

```text
DecisionResult (CatedralX)
        |
        | transporte/invocación; no es aceptación
        v
Candidate (Agents, persistido)
        |
        | revisión explícita e independiente
        v
Acceptance decision
   |             |
   | accepted    | rejected
   v             v
Acceptance      Rechazo registrado
verificada      sin distribución
   |
   | gate de distribución
   v
Distribution elegible
```

Ninguna transición implica ejecución de una orden. `analysis_only=true`, `orders_created=false` y `orders_executed=false` permanecen como restricciones del DecisionResult actual.

## 7. Discrepancias y decisiones abiertas

| ID | Hallazgo | Tratamiento |
|---|---|---|
| C-01 | `evaluation_hash` es obligatorio y no nullable en el schema actual | Mantenerlo así hasta una migración explícita |
| C-02 | DecisionResult permite patrón de trace ID de 32 hex, pero no prohíbe cero | Añadir prueba y decidir si endurecer schema en cambio separado |
| C-03 | Acceptance firma diez campos con serialización propia; no RFC 8785 | Documentar implementación actual; no sustituirla sin migración |
| C-04 | El payload Acceptance no incluye `result_id` | Formalizar enlace Candidate↔DecisionResult fuera del payload firmado o versionar el payload |
| C-05 | DecisionResult schema no prohíbe propiedades adicionales | Decidir política de extensibilidad antes de cerrar el schema |
| C-06 | Schema y validadores de Acceptance aplican reglas distintas y en capas | Crear pruebas de contrato compartidas; no asumir que un schema reemplaza las validaciones semánticas |

## 8. Pruebas de contrato requeridas antes de cambiar código

### DecisionResult
- instancia válida para cada estado;
- ausencia de cada campo obligatorio;
- `evaluation_hash` ausente, nulo, formato incorrecto y SHA-256 válido;
- `trace_id` mal formado, mayúsculas y todos ceros;
- `analysis_only=false`, `orders_created=true`, `orders_executed=true);
- estado `ACCEPTED` con evidencia o provenance vacía;
- propiedades adicionales, conforme a la política que se decida.

### Acceptance
- payload aceptado válido y rechazado válido;
- cada uno de los diez campos ausente;
- campo extra;
- outcome desconocido;
- accepted sin criterios, con razones o con evidencia faltante;
- rejected sin razón ni evidencia faltante;
- identidad de verificador incorrecta;
- timestamp sin zona horaria;
- trace ID inválido, cero o distinto al del candidato;
- digest distinto de la evidencia recalculada;
- firma alterada, firma de longitud incorrecta y clave pública inválida;
- confirmación humana ausente o ligada a otro candidato;
- repetición idéntica de `decision_id`, conflicto del mismo ID y segunda decisión para el mismo candidato.

### Integración
- preservar el mismo `trace_id` en resultado, candidato y decisión;
- probar explícitamente el enlace `result_id → candidate_id` cuando se defina;
- demostrar que un Candidate no aceptado no se distribuye;
- demostrar que Acceptance no crea ni ejecuta órdenes;
- distinguir pruebas unitarias/contractuales de una prueba E2E runtime.

## 9. Fuentes primarias

- [JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12)
- [RFC 8785 — JSON Canonicalization Scheme](https://www.rfc-editor.org/rfc/rfc8785)
- [RFC 8032 — EdDSA / Ed25519](https://www.rfc-editor.org/rfc/rfc8032)
- [W3C Trace Context Recommendation](https://www.w3.org/TR/trace-context/)
- [DecisionResult schema en CatedralX](https://github.com/Chalamandra-Magistral-deco/CatedralX/blob/main/elite/contracts/schemas/decision_result.json)
- [Acceptance verifier en Agents](https://github.com/Chalamandra-Magistral-deco/chalamandra-agent-engine/blob/main/verifier/independent_acceptance_verifier.py)
- [Acceptance API signer/verifier en Agents](https://github.com/Chalamandra-Magistral-deco/chalamandra-agent-engine/blob/main/api/crypto_signer.py)
- [Acceptance store en Agents](https://github.com/Chalamandra-Magistral-deco/chalamandra-agent-engine/blob/main/api/acceptance_store.py)

---

**Límite de esta entrega:** se añadió documentación de contrato en una rama de trabajo de CatedralX. No se modificó el JSON Schema ejecutable, el código de Agents, las claves, los flujos de distribución ni la configuración de despliegue. No se ha afirmado ni ejecutado una prueba E2E.
