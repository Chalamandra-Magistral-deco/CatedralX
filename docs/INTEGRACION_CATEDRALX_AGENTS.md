# Integración CatedralX ↔ Agents

**Actualizado:** 28 de octubre de 2026
**Objetivo:** CatedralX conserva la lógica canónica de decisión. Agents/API son interfaces de recepción, ejecución controlada, trazabilidad y entrega; no sustituyen ni duplican el motor central.

## Flujo y límites

1. CatedralX registra el ciclo económico: `measure → evaluate → propose → authorize`.
2. El despacho a Agents es explícito; el motor no lo inicia automáticamente y así evita recursión. La lectura y validación del ciclo autorizado se centraliza en `FEX.GOVERNANCE.economic_cycle.cargar_propuesta_autorizada`; el CLI solo adapta el resultado a la API.
3. Agents autentica la solicitud, registra la tarea en TaskBus y llama al punto de entrada canónico de CatedralX para análisis financieros.
4. El resultado se conserva como candidato con evidencia y procedencia. No se entrega como aceptado hasta superar el gate independiente de aceptación.
5. Los límites de ejecución prohíben publicaciones, contacto externo, gasto publicitario, compras, órdenes financieras y reinversión automática.

**Configuración de seguridad:** llamadas a modelos desactivadas por defecto (`execution_enabled=false`). No se habilitan operaciones comerciales reales ni trading mediante esta integración. Conservar los umbrales canónicos `THETA_E=8500` y `THETA_GLOBAL=7000`.

## Despacho explícito de un ciclo autorizado

```bash
BIN/catedral dispatch-agents --cycle-id ID_DEL_CICLO
```

Opcionalmente, especifica el ledger:

```bash
BIN/catedral dispatch-agents \
  --cycle-id ID_DEL_CICLO \
  --ledger-path /ruta/segura/impact_cycle.jsonl
```

El ledger debe contener exactamente las cuatro etapas indicadas para ese `cycle_id`, con payloads válidos y `authorize.payload.approved=true`, `approver` y `rationale` no vacíos. El comando rechaza etapas ausentes, adicionales o malformadas. La clave de idempotencia deriva del identificador del ciclo para que los reintentos no creen tareas duplicadas.

Para otra tarea de análisis expresamente invocada:

```bash
BIN/catedral dispatch-agents \
  --objective financial_analysis \
  --payload-file /ruta/segura/observacion.json \
  --idempotency-key ID_ESTABLE_DE_LA_TAREA
```

El modo `--objective` no constituye autorización comercial ni sustituye los controles de cada flujo.

## Configuración

- `CHALAMANDRA_JWT_SECRET`: secreto JWT requerido por la API; no imprimirlo ni guardarlo en el repositorio.
- `CHALAMANDRA_API_URL`: opcional; por defecto `http://127.0.0.1:8766`. HTTP sin TLS solo se permite en loopback.
- `CATEDRALX_PATH`: ruta al checkout canónico desde el worker si no está en la ubicación relativa esperada.
- `CATEDRALX_STATE_PATH` y `CATEDRALX_FEEDBACK_PATH`: estado y feedback fuera del checkout.

El payload financiero debe contener al menos 30 precios positivos y finitos, `current_price`, `observed_at` ISO-8601 con zona horaria y `source`. Se rechazan timestamps inválidos, futuros o con antigüedad superior a 120 segundos. `source` es metadato declarado, no prueba criptográfica del origen del feed.

## Validación automatizada

Las pruebas de integración usan fixtures sintéticos y verifican API HTTP, autenticación, TaskBus, worker, invocación del motor canónico, trazabilidad, límites de ejecución y aceptación independiente.

```bash
# En agents/
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. venv/bin/python -m pytest -q -p no:cacheprovider

# En CatedralX/
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m pytest -q -p no:cacheprovider
```

Última validación local: **Agents 180 passed; CatedralX 303 passed**. Ruff pasa en los archivos activos de integración; la ejecución sobre todo CatedralX detecta deuda de estilo histórica en `docs/legacy`, AEX y tests antiguos, no corregida masivamente para evitar una reescritura de archivos ajenos al cambio. Esto demuestra pruebas de software con datos sintéticos; no demuestra demanda, ingresos, validez predictiva ni autenticidad de datos externos.

## Estado operativo y pendientes

- API productiva: contenedor `chalamandra-api`, puerto local `127.0.0.1:8766`; `/healthz` responde HTTP 200 con ejecución de modelos desactivada.
- Worker persistente: `chalamandra-worker.service`; se reinició de forma controlada tras comprobar que no había tareas `queued` o `running`.
- La API se actualizó en el contenedor existente para conservar variables y montajes. La etiqueta de imagen del contenedor no representa por sí sola ese filesystem actualizado; no recrearlo desde una imagen anterior sin promover primero una imagen inmutable y preservar el volumen de estado.
- No se encontró un ciclo económico autorizado en el ledger predeterminado; no se inventó aprobación ni se despachó una propuesta comercial real.
- El endpoint local de estado de CatedralX en `127.0.0.1:5050` no estaba escuchando y debe resolverse explícitamente.
- La aceptación basada en HMAC compartido no demuestra separación criptográfica real; falta conectar identidad y claves independientes Ed25519.
- La autenticación JWT debe endurecerse con `iss`/`aud` y una identidad de servicio bien delimitada.
- El origen del feed debe autenticarse por separado del campo textual `source`.
- Antes de producción plena: construir/promover imagen inmutable mediante gestión segura de secretos, conservar el volumen y probar rollback. No exportar secretos a archivos ni incorporarlos a la imagen.

## Política de cambio

No ejecutar `reset`, `pull`, `merge`, borrado masivo, publicación ni operaciones comerciales sin comparar primero el estado local y remoto y validar los efectos. Mantener los cambios locales hasta revisión y aprobación explícita de la publicación.
