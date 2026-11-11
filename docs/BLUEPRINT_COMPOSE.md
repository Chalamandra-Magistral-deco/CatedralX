# Blueprint de Topología — Docker Compose

**Estado:** arquitectura objetivo; no es un despliegue listo.
**Origen:** sesión de consolidación 2026-10-25.

> **Distinción vigente (2026-11-11):** el `docker-compose.yml` de la raíz del repositorio solo ejecuta la imagen CLI de CatedralX en modo puntual (`catedral status`). No implementa esta topología multi-servicio, no publica una API ni levanta Redis, Agents o workers. La configuración raíz se valida en CI; este blueprint sigue siendo una propuesta futura.

## Servicios objetivo

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
- catedralx-state — estado persistente de CatedralX
- FALTA: volumen para result_store
- FALTA: volumen para webhook queue

## Pendiente del blueprint

- TLS reverse proxy en red edge
- Secrets management (Vault/rotación)
- Health checks de api, catedralx, agent-worker
- Dockerfiles reales para las imágenes de API y worker
- Contratos de persistencia y aceptación para cada servicio
- Pruebas E2E en un destino de ejecución autorizado

## Contenido completo

Ver [BLUEPRINT_COMPOSE_FULL.yaml](BLUEPRINT_COMPOSE_FULL.yaml) para el YAML de referencia.
