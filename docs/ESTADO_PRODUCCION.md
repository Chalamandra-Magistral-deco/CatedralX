# Estado de Producción — Chalamandra Magistral

**Fecha de corte:** 2026-10-25
**Responsable:** Auditoría técnica de consolidación

## 1. Hito Alcanzado: Backend Determinista y API Distribuida

El núcleo de Chalamandra Magistral (CatedralX) y la Malla de Agentes (API) han sido construidos, probados y desplegados en la VM de Azure.

### Repositorios (Sincronizados en `origin/main`)
- **CatedralX** (`cc0d3f8`): 286 tests passed.
- **agents** (`7303b8a`): 141 tests passed.

### Infraestructura y Despliegue
- **Servicio Local:** `chalamandra-agents-api.service` corriendo bajo systemd (loopback `127.0.0.1:8766`).
- **Túnel Cloudflare:** `motor-chalamandra` activo con 3 conexiones Edge (dfw06, dfw15, dfw19).
- **Dominio Público:** `https://api.chalamandramagistral.com` responde `HTTP 200` (verificado con token real).
- **Seguridad:** Token Bearer rotado, journal purgado, `cert.pem` asegurado (chmod 600), túnel huérfano (`chalamandrax-tunnel`) eliminado.
- **Model Calls:** Habilitado (`true`) justificado para los 3 flujos DecoX; la seguridad recae en el Gate de Aceptación.

## 2. Arquitectura Implementada

- **Plano de Control:** CatedralX (motor determinista, sin alucinaciones).
- **Plano de Evidencia:** `result_store`, `acceptance_store`, `task_bus`. Trazabilidad completa vía `X-Trace-Id`.
- **Plano de Entrega:** API expuesta de forma segura con Gate de Aceptación independiente.
- **Modos DecoX:**
  - Modo 1 (Reactivo): `POST /v1/jobs` -> CatedralX -> `DecisionResult`.
  - Modo 2 (Retorno): `POST /v1/acceptance` -> Webhooks (SSRF protegido).
  - Modo 3 (Proactivo): `POST /internal/v1/orchestration/runs` -> Task Bus -> Worker.

## 3. Checklist Estratégico (Actualizado)

- [x] **P1 — Validar agentes y contratos de ejecución:** Suite termina en verde (427 tests), trazabilidad y separación de poderes verificada.
- [x] **P0 — Cerrar inventario maestro (Backend):** API vinculada a Cloudflare Tunnel y VM. (Faltan dominios de Frontend).
- [ ] **P0 — Verificar captación y persistencia de leads:** Pendiente (requiere auditoría de repos Frontend).
- [ ] **P0 — Cerrar la ruta de compra y entrega:** Pendiente (requiere pasarela de pago).
- [ ] **P1 — Verificar seguridad y publicación de Tricentric:** Pendiente.
- [ ] **P1 — Activar medición comercial fiable:** Pendiente.
- [ ] **P2 — Optimizar y escalar el embudo:** Pendiente.

## 4. Próximos Pasos
1. Auditar los repos Frontend (`OMNI-CHALAMANDRA`, `CHMADEX-DIAL`, etc.) para vincular los 7 dominios oficiales.
2. Definir SystemDecode como consumidor de los webhooks del Modo 2.
3. Dockerizar el backend usando el `BLUEPRINT_COMPOSE_FULL.yaml`.
