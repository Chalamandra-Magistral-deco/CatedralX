# Arquitectura Objetivo — Chalamandra Magistral

**Estado:** Diseño cerrado, implementación parcial
**Última actualización:** 2026-10-25

## 1. Los 3 Planos Arquitectónicos

### 1.1 Plano de Control (CatedralX)
- **Rol:** Gobernanza, motor determinista, evaluación de criterios de aceptación
- **Autoridad:** Ningún modelo generativo o agente LLM puede sobrescribir las reglas
- **Implementación:** elite/REASON/orchestrator.py, elite/contracts/actions.py, elite/REASON/cognitive_state.py

### 1.2 Plano de Evidencia (Registro y Verificación)
- **Rol:** Trazabilidad completa, procedencia, contraevidencia, pruebas
- **Regla invariable:** Una afirmación no es un hecho verificado por el simple acto de ser generada por un agente
- **Implementación:** elite/FEX/FEEDBACK/feedback_loop.py, elite/FEX/GOVERNANCE/sustainability.py, elite/MSX/provenance.py

### 1.3 Plano de Entrega (Membrana API)
- **Rol:** Punto de entrada/salida seguro, validación de contratos, autorización
- **Implementación:** elite/bin/inyector-vitral (CatedralX), agents/api/server.py (agents)

## 2. Los 3 Modos de Causalidad

### 2.1 Modo 1 — Reactivo / Síncrono
Usuario → API → CatedralX → Agentes → Verificación → API → Usuario

### 2.2 Modo 2 — Retorno / Asíncrono
CatedralX → Agentes → Verificación → API → Notificación
Conserva job_id + trace_id.

### 2.3 Modo 3 — Proactivo / Por Eventos
Scheduler/Evento → CatedralX → Agentes → Verificación → Alerta

## 3. Las 5 Garantías Arquitectónicas

1. **CatedralX dirige:** Define criterios, autoriza alcance, aplica reglas explícitas
2. **Los agentes proponen:** CandidateResult != AcceptanceDecision. No se auto-aceptan
3. **La verificación evalúa:** AcceptanceDecision viene de verificador independiente con criterios versionados
4. **La API controla la entrega:** HTTP 200 != ACCEPTED. Valida contrato, permisos y aceptación antes de publicar
5. **Los 3 modos comparten trazabilidad:** job_id identifica la tarea, trace_id enlaza eventos y evidencias

## 4. Principio de Aceptación Explícita

Un resultado técnicamente correcto NO se convierte automáticamente en un resultado autorizado.

- needs_evidence, rejected, blocked NO se publican como accepted
- UNCERTAIN no es fallo técnico: es ejecución satisfactoria sin evidencia suficiente
- El verificador independiente decide, no el worker que generó el candidato

## 5. Estado de Implementación (2026-10-25)

| Componente | Estado |
|---|---|
| CatedralX motor determinista | ✅ 281 tests verdes |
| agents workers + tool registry | ✅ 132 tests verdes |
| Circuito API->agents->CatedralX | ⚠️ Inicial (sin gate independiente) |
| AcceptanceDecision | ❌ Pendiente |
| Modo 2 (Retorno async) | ❌ Pendiente |
| Modo 3 (Proactivo) | ❌ Pendiente |
| result_store persistente | ❌ Pendiente |
| JWT user/service | ❌ Pendiente |
| Redis queue | ❌ Pendiente |
| Dockerfiles + TLS | ❌ Pendiente |

## 6. Contratos OpenAPI

- contracts/request_flow.yaml — Entrada pública (jobs, results) — NO IMPLEMENTADO
- contracts/distribution_flow.yaml — Salida pública (subscriptions, webhooks) — NO IMPLEMENTADO
- contracts/orchestration_flow.yaml — Orquestación interna (runs, acceptance) — NO IMPLEMENTADO

## 7. Referencias

- Especificación original §1-§6
- AUDITORIA_CONSOLIDACION_PERGAMINO.md — auditoría formal de CatedralX
- PROMPT_AGENTS.md — contrato maestro de AGENTS (en repo agents)
Conserva job_id + trace_id.

### 2.3 Modo 3 — Proactivo / Por Eventos
Scheduler/Evento → CatedralX → Agentes → Verificación → Alerta

## 3. Las 5 Garantías Arquitectónicas

1. **CatedralX dirige:** Define criterios, autoriza alcance, aplica reglas explícitas
2. **Los agentes proponen:** CandidateResult != AcceptanceDecision. No se auto-aceptan
3. **La verificación evalúa:** AcceptanceDecision viene de verificador independiente con criterios versionados
4. **La API controla la entrega:** HTTP 200 != ACCEPTED. Valida contrato, permisos y aceptación antes de publicar
5. **Los 3 modos comparten trazabilidad:** job_id identifica la tarea, trace_id enlaza eventos y evidencias

## 4. Principio de Aceptación Explícita

Un resultado técnicamente correcto NO se convierte automáticamente en un resultado autorizado.

- needs_evidence, rejected, blocked NO se publican como accepted
- UNCERTAIN no es fallo técnico: es ejecución satisfactoria sin evidencia suficiente
- El verificador independiente decide, no el worker que generó el candidato

## 5. Estado de Implementación (2026-10-25)

| Componente | Estado |
|---|---|
| CatedralX motor determinista | ✅ 281 tests verdes |
| agents workers + tool registry | ✅ 132 tests verdes |
| Circuito API->agents->CatedralX | ⚠️ Inicial (sin gate independiente) |
| AcceptanceDecision | ❌ Pendiente |
| Modo 2 (Retorno async) | ❌ Pendiente |
| Modo 3 (Proactivo) | ❌ Pendiente |
| result_store persistente | ❌ Pendiente |
| JWT user/service | ❌ Pendiente |
| Redis queue | ❌ Pendiente |
| Dockerfiles + TLS | ❌ Pendiente |

## 6. Contratos OpenAPI

- contracts/request_flow.yaml — Entrada pública (jobs, results) — NO IMPLEMENTADO
- contracts/distribution_flow.yaml — Salida pública (subscriptions, webhooks) — NO IMPLEMENTADO
- contracts/orchestration_flow.yaml — Orquestación interna (runs, acceptance) — NO IMPLEMENTADO

## 7. Referencias

- Especificación original §1-§6
- AUDITORIA_CONSOLIDACION_PERGAMINO.md — auditoría formal de CatedralX
- PROMPT_AGENTS.md — contrato maestro de AGENTS (en repo agents)

## 8. Nota sobre `CHALAMANDRA_API_ENABLE_MODEL_CALLS`

**Decisión:** Este flag debe permanecer en `true` en producción.

**Razón:** Los 3 flujos DecoX (Normal, Inverso, Invertido) requieren que los agentes especializados usen LLMs para:
- Modo 1: Investigar y buscar contraevidencia.
- Modo 2: Contextualizar resultados cacheados.
- Modo 3: Ejecutar tareas proactivas.

**Seguridad:** La separación de poderes no se logra apagando los LLMs, sino mediante:
1. CatedralX (núcleo determinista) que define las reglas.
2. El Gate de Aceptación (Fase 2) que exige firma independiente.
3. El aislamiento de red (loopback + NSG) que impide acceso externo.

Un agente puede investigar con LLM, pero **no puede autorizar su propio resultado**.

## 9. Actualización post-auditoría (2026-10-25)

El estado anterior de este documento indicaba "implementación parcial". Tras las correcciones de auditoría (commits `cdc15c2` y `330a3de` en `agents`), el estado real es:

- **Los 3 modos** (Reactivo, Retorno, Proactivo) están unificados a través del TaskBus SQLite.
- **El Gate de Aceptación** exige firma HMAC y valida el `evidence_digest` SHA-256 contra el candidato almacenado.
- **El Worker persistente** procesa tareas reales (no simuladas) y genera evidencia verificable.
- **Todas las rutas** exigen JWT con `exp` y scopes específicos.
- **Fail-closed:** `task_validator` devuelve `NOT_EVALUATED` y `executor` exige `is_pass`.

La deuda técnica restante (Ed25519, Redis, Docker/TLS, JWT `iss`/`aud`, worker token) está documentada en `ESTADO_PRODUCCION.md` §4.
