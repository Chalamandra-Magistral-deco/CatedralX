# FLUJOS_SISTEMA — CatedralX

## Entrada canónica

`BIN/catedral` orquesta los comandos `status`, `feed-once`, `motor`, `ciclo`, `impact-cycle`, `user-feedback`, `dispatch-agents` y `test`.
`docs/legacy/motor.py` es un wrapper histórico/deprecado; no es la entrada canónica.

## Fuentes de estado separadas

- **Snapshot RSX:** `CATEDRALX_SNAPSHOT_PATH`; por defecto `/dev/shm/cathedral_snapshot.json`, leído y escrito por `PERCEIVE.data_feeder`. Contiene observaciones recibidas; no debe rellenarse con datos sintéticos.
- **Estado persistente:** `CATEDRALX_STATE_PATH`; por defecto `~/.local/state/chalamandra/catedralx/hormonas.json`, gestionado por `REASON.state_paths`.
- **Feedback de usuario:** `CATEDRALX_USER_FEEDBACK_PATH`; por defecto `~/.local/state/chalamandra/catedralx/user_feedback.jsonl`.
- **Resultados:** `CATEDRALX_RESULT_STORE_PATH`; por defecto `~/.local/state/chalamandra/catedralx/results.jsonl`.

Estas rutas cumplen funciones distintas; no son duplicados. Los datos persistentes deben permanecer fuera del checkout.

## Flujo de razonamiento

`PERCEIVE` valida y entrega observaciones.
`REASON.orchestrator.execute_cycle` construye el ciclo cognitivo y sus diagnósticos.
Los contratos de `elite/contracts` normalizan acciones y construyen/validan resultados trazables.
Los gates de gobernanza y defensa pueden bloquear el flujo. Una etiqueta `buy`, `sell` o `hold` es análisis, no una orden.

## NEXUS y endpoint loopback

`elite/bin/nexus.py status()` expone el estado resumido del motor.
El endpoint opcional de solo lectura está implementado en `elite/bin/inyector-vitral`: sirve `/status` y `/health` en `127.0.0.1:5050` cuando se ejecuta explícitamente.

**No forma parte del contenedor CLI predeterminado.** La imagen Docker ejecuta `catedral status` y termina; por ello el Compose de este repositorio no publica el puerto 5050 ni reinicia el contenedor como daemon. Para exponer un servicio se requiere un diseño separado de bind interno, mapeo loopback, ciclo de vida y pruebas; no se debe inferir que el endpoint está desplegado.

## Límites de seguridad

- `trading_enabled=false`, `orders_created=false` y `orders_executed=false` son los límites de análisis documentados.
- El despacho a Agents es explícito y requiere el ciclo autorizado o una invocación de análisis expresamente permitida.
- Las pruebas sintéticas y CI no prueban conexión en runtime con Agents ni despliegue productivo.

## Evidencia y vigencia

Los snapshots operativos, conteos de pruebas y observaciones de mercado de octubre de 2026 son históricos; no describen un runtime actual. La evidencia vigente de pruebas y construcción está en [ESTADO_PRODUCCION.md](ESTADO_PRODUCCION.md). La VM anterior no forma parte del plan operativo.
