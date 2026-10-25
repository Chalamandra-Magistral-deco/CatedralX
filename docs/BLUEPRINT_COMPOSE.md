# Blueprint de Topología — docker-compose

**Estado:** BLUEPRINT, no despliegue listo.
**Origen:** Sesión de consolidación 2026-10-25.

## Servicios

| Servicio | Propósito | Perfil |
|---|---|---|
| redis | Cola de jobs + bus de eventos | siempre |
| api | Membrana API (Request + Distribution + Orchestration) | app |
| catedralx | Motor determinista | app |
| agent-worker | Workers de agentes | app |

## Redes

- control (internal: true) — comunicación interna
- edge (bridge) — solo api expuesto para TLS reverse proxy

## Volúmenes

- redis-data — persistencia append-only de Redis
- catedralx-state — /var/lib/chalamandra/catedralx/hormonas.json
- FALTA: volumen para result_store
- FALTA: volumen para webhook queue

## Pendiente del blueprint

- TLS reverse proxy en red edge
- Secrets management (Vault/rotación)
- Health checks de api, catedralx, agent-worker
- Dockerfiles reales para las 3 imágenes

## Contenido completo

Ver docs/BLUEPRINT_COMPOSE_FULL.yaml para el YAML completo.
