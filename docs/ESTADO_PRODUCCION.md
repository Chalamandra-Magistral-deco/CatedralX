# Estado de Producción — Chalamandra Magistral

**Fecha de corte:** 2026-10-25 (post-auditoría externa)
**Auditor:** Autor del Pergamino

## 1. Hito alcanzado: Backend unificado y auditado

Los tres flujos DecoX están unificados a través de un TaskBus atómico (SQLite) y un Worker persistente que ejecuta tareas reales.

### Repositorios (sincronizados en origin/main)
- **CatedralX** (`3a81158`): 286 tests.
- **agents** (`330a3de`): 145 tests.

### Infraestructura y despliegue
- **Servicio API:** `chalamandra-agents-api.service` (activo, loopback `127.0.0.1:8766`).
- **Servicio Worker:** `chalamandra-worker.service` (activo, procesa TaskBus).
- **Túnel Cloudflare:** `motor-chalamandra` (activo, 3 conexiones Edge).
- **Dominio público:** `https://api.chalamandramagistral.com` responde `HTTP 200`.

## 2. Arquitectura implementada

### Planos y flujos
- **Plano de Control:** CatedralX (motor determinista).
- **Plano de Evidencia:** `result_store`, `acceptance_store` (HMAC), `candidate_store` (SHA-256), `task_bus` (SQLite atómico).
- **Plano de Entrega:** API con JWT y scopes, webhooks firmados.

### Flujos DecoX (unificados)
- **Modo 1 (Reactivo):** `POST /v1/jobs` → TaskBus → Worker → CatedralX/Master → `DecisionResult`.
- **Modo 2 (Retorno):** `POST /v1/acceptance` (firma HMAC + validación SHA-256) → Webhook firmado.
- **Modo 3 (Proactivo):** `POST /internal/v1/orchestration/runs` → TaskBus → Worker persistente.

## 3. Correcciones post-auditoría (P0/P1/P2)

- **P0 (Autorización):** Todas las rutas exigen JWT con `exp` y scopes. `/healthz` es público.
- **P0 (Contrato unificado):** `job_manager` acepta formato anidado (`{"type": ..., "payload": {...}}`) y plano.
- **P1 (TaskBus atómico):** Migrado a SQLite con `BEGIN IMMEDIATE`. Test de concurrencia con 5 hilos (solo 1 gana).
- **P1 (Worker real):** Ejecuta `Master.execute_task()` o CatedralX según la tarea. Genera evidencia SHA-256.
- **P1 (Aceptación estricta):** Valida `evidence_digest` contra el candidato almacenado.
- **P1 (Webhooks firmados):** HMAC + SSRF revalidado por entrega.
- **P1 (Fail-closed):** `SKIPPED` → `NOT_EVALUATED`. `executor` exige `is_pass`.
- **P2 (W3C Trace Context):** Parser estricto con regex.

## 4. Deuda técnica documentada

| Componente | Estado | Razón |
| :--- | :--- | :--- |
| **Ed25519 (firma asimétrica)** | Pendiente | HMAC exige que la API tenga el secreto. Ed25519 (clave privada fuera de la API) es la solución correcta para separación criptográfica real. |
| **Redis (broker distribuido)** | Pendiente | SQLite funciona para una VM. Redis será necesario para escalado horizontal. |
| **Docker/TLS** | Pendiente | Existe `BLUEPRINT_COMPOSE_FULL.yaml` pero faltan Dockerfiles reales. |
| **JWT con `iss`/`aud`** | Pendiente | Actualmente solo valida `exp` y `scope`. Falta validación de emisor y audiencia. |
| **Worker identidad diferenciada** | Pendiente | El worker usa el mismo token que el usuario. Debería tener un token de servicio con scope `worker:write`. |

## 5. Checklist estratégico actualizado

- [x] **P1 — Validar agentes y contratos de ejecución:** 145 tests verdes. Fail-closed. Trazabilidad W3C.
- [x] **P0 — Inventario maestro (Backend):** API vinculada a Cloudflare Tunnel.
- [ ] **P0 — Captación y persistencia de leads:** Pendiente (Frontend).
- [ ] **P0 — Ruta de compra y entrega:** Pendiente (Frontend).
- [ ] **P1 — Seguridad y publicación de Tricentric:** Pendiente.
- [ ] **P1 — Medición comercial fiable:** Pendiente.
- [ ] **P2 — Optimizar y escalar el embudo:** Pendiente.

## 6. Próximos pasos

1. **Frontend (P0):** Auditar `OMNI-CHALAMANDRA`, `CHMADEX-DIAL`, etc. para conectar leads y checkout.
2. **Ed25519:** Migrar de HMAC a firma asimétrica para separación criptográfica real.
3. **SystemDecode:** Conectar el consumidor de webhooks del Modo 2.
4. **Docker/TLS:** Crear Dockerfiles y migrar a despliegue con contenedores.
