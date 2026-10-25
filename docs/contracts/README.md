# Contratos OpenAPI — Chalamandra Magistral

**Estado:** Diseñados, NO IMPLEMENTADOS.

| Archivo | Propósito |
|---|---|
| request_flow.yaml | Entrada pública: POST /v1/jobs, GET /v1/jobs/{id}, GET /v1/results/{id} |
| distribution_flow.yaml | Salida pública: subscriptions + webhooks + SSRF |
| orchestration_flow.yaml | Orquestación interna: runs + tasks + acceptance |

## Verificación de implementación

Ninguno de los 3 contratos tiene código que los implemente. Verificado con:

- grep job_id /v1/jobs Idempotency-Key -> 0 resultados en agents/
- grep subscription webhook endpoint_url -> 0 resultados en ambos repos
- grep AcceptanceDecision -> 0 resultados en ambos repos

## Estado real de implementación

| Componente | Estado |
|---|---|
| CatedralX motor | ✅ 281 tests verdes |
| agents workers | ✅ 132 tests verdes |
| AcceptanceDecision | ❌ 0% |
| Modo 2 (Retorno async) | ❌ 0% |
| Modo 3 (Proactivo) | ❌ 0% |
| result_store persistente | ❌ 0% |
| JWT user/service | ❌ 0% |
| Redis queue | ❌ 0% |
| Dockerfiles + TLS | ❌ 0% |

## Referencias

- docs/ARQUITECTURA_OBJETIVO.md — arquitectura completa
- docs/BLUEPRINT_COMPOSE.md — topología docker-compose
