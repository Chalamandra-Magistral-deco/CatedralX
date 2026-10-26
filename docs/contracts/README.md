# Contratos OpenAPI — Chalamandra Magistral DecoX

**Revisión de código:** 2026-10-26.  
Los contratos describen el comportamiento deseado; tener rutas con nombres similares no prueba conformidad ni despliegue.

| Contrato | Función objetivo | Estado observado |
|---|---|---|
| `request_flow.yaml` | Crear trabajos, consultar estado y recuperar resultados aceptados. | **Parcial.** Existen rutas `/v1/jobs`, `/v1/jobs/{id}` y `/v1/results/{id}`; no se verificó el recorrido real hasta aceptación independiente. |
| `distribution_flow.yaml` | Crear/listar/deshabilitar suscripciones y distribuir solo resultados aceptados. | **Parcial.** Existen `subscription_store` y `webhook_dispatcher`; no se confirmó `POST /v1/subscriptions`. Hay desajustes de scopes y falta revisar la defensa SSRF ante redirecciones. |
| `orchestration_flow.yaml` | Disparar runs, consultar estado y recibir resultados del worker con token de servicio. | **P0 en main.** GET de runs no valida su scope y consulta métodos inexistentes; POST de resultados no valida autorización. La corrección está propuesta en [PR #13](https://github.com/Chalamandra-Magistral-deco/chalamandra-agent-engine/pull/13), aún no fusionada. |

## Componentes relacionados

- **TaskBus:** SQLite, reserva de tareas e idempotencia existen en `api/task_bus.py`.
- **Candidate store:** persiste candidatos y calcula un digest SHA-256 de evidencia.
- **Acceptance store:** usa HMAC-SHA256 y contrasta el digest. Esto depende de un secreto compartido, no demuestra firma asimétrica independiente.
- **Ed25519:** `api/crypto_signer.py` existe, pero el flujo de aceptación no lo utiliza y PyNaCl no está declarada en los manifiestos revisados.
- **Worker:** el código existe en `api/worker_loop.py`; el servicio activo en VM no se ha verificado.
- **Modo proactivo:** existe endpoint interno de disparo; scheduler desplegado no comprobado.

## Criterio de finalización

Un flujo solo pasa a “validado” cuando el endpoint comprueba el scope correcto, el payload satisface el schema, el recorrido se ejecuta de extremo a extremo, IDs/evidencia/digest/aceptación son coherentes, el CI está verde en el commit exacto y el despliegue real se inspecciona. No declarar los tres contratos implementados solo porque existan rutas o módulos.
