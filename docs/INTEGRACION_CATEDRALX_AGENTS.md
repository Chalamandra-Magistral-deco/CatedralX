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

## Addendum de verificación — 2026-10-28

Esta sección complementa el registro previo; no elimina ni sustituye los cambios locales anteriores.

- Las pruebas actuales ejecutadas con CATEDRALX_PATH explícito fueron: **Agents 199 passed** y **CatedralX 308 passed** con el dispatcher autorizado existente. Ruff y git diff --check pasan en los archivos de integración y scheduler revisados.
- Se verificó elite/bin/dispatch_authorized_cycles.py como ejecutor de una pasada: consulta el ledger canónico, descubre ciclos cuya secuencia de eventos es exactamente measure → evaluate → propose → authorize y exige aprobación humana. Usa catedralx-economic-cycle:<cycle_id> como clave idempotente y registra intentos/recibos en dispatches.jsonl fuera del checkout.
- Se corrigió el import del dispatcher autorizado para que las pruebas lo carguen desde tests y se ajustaron sus avisos de Ruff. La suite dirigida del dispatcher y su CLI dio 12 passed; el timer candidato pasó systemd-analyze verify. Los archivos de unidad están en deploy/systemd, pero no están instalados ni habilitados.
- La ejecución real --dry-run con la ruta predeterminada no pudo iniciarse porque aún no existe ~/.local/state/chalamandra/catedralx/impact_cycle.jsonl. No se inventó un ciclo productivo ni se modificó el ledger.
- No hay systemd --user timer de despacho ni crontab del usuario. Tampoco está presente el archivo de entorno propuesto para el secreto de despacho. Por tanto, el scheduler está implementado y probado por fixtures, pero **no está activado como servicio**.
- Se confirma que POST /v1/jobs es la ruta de solicitud normal; el flujo originado por CatedralX utiliza POST /internal/v1/orchestration/runs. POST /v1/request no está implementado en el server.py revisado.
- La API productiva observada continúa en la imagen chalamandra-agent-engine:backup-pre-e6d67db, saludable, con llamadas de modelos desactivadas; el worker de usuario continúa activo. La imagen candidata chalamandra-agents:security-canary-v2-20261028 se conserva aparte y no ha sido promovida.
- La nueva verificación Ed25519 e identidad fijada existe en el checkout local y pasó su batería de pruebas; no debe interpretarse como activada en producción. No se reinició ni recreó el contenedor productivo, no se cambió su entorno, no se hizo commit ni push.
- El reconciliador agents/api/catedralx_feedback.py está implementado y tiene pruebas: vuelve a verificar firma Ed25519, identidad y digest de evidencia; vincula el candidato con business_cycle_id y registra verify → feedback en el ledger económico canónico. El registro indica expresamente que el impacto comercial no ha sido medido; aceptación estructural no se interpreta como ingreso o demanda. Su unidad systemd es candidata y no está instalada ni activa.
- Próximo bloqueo de activación: elegir y provisionar el ledger de ciclos, configurar el secreto de servicio fuera del repositorio, instalar y observar el timer con una prueba sintética, definir el contrato de feedback de entrega separado del feedback de mercado y después repetir los tres flujos con evidencia persistente de firma Ed25519 y traza W3C.

No habilitar el timer ni promover la imagen hasta que los prerrequisitos anteriores pasen validación en el entorno aislado.


## Addendum correctivo de cierre — 2026-10-28

Este addendum reemplaza los conteos de prueba anteriores de esta documentación; conserva intacto el historial de decisiones.

- **Agents:** suite completa ejecutada en `~/workspace/repos/agents`: **200 passed**.
- **CatedralX:** suite completa ejecutada en `~/workspace/repos/CatedralX`: **310 passed**. Se corrigió un test legado para que el escenario simulado suministre el `evaluation_hash` que ahora exige el contrato central; no se relajó el requisito de producción.
- **Estilo y whitespace:** Ruff pasó en los archivos de integración modificados de ambos repositorios; `git diff --check` pasó en ambos. No se declara que Ruff esté limpio en todos los archivos históricos del repositorio.
- **API local del checkout:** `POST /v1/request` utiliza autenticación con alcance `jobs:write`, clave de idempotencia y propagación de `traceparent` W3C. La traza evita registrar cuerpo, Authorization y query strings. Se cubre con pruebas HTTP y de integración en entorno temporal.
- **Aceptación:** los registros Ed25519 se almacenan separadamente en `acceptance_store.jsonl`; las lecturas verifican firma, identidad del verificador y digest del candidato. Las aceptaciones exactas son idempotentes; decisiones contradictorias fallan de forma cerrada. La aceptación heredada HMAC no se promueve automáticamente como evidencia Ed25519.
- **Evaluación CatedralX:** el contrato requiere `evaluation_hash` SHA-256, `evaluation_gate`, `cycle_id` y `trace_id` W3C. La política usa puntuaciones en basis points, `Decimal`, umbrales de evidencia 8500 y puntuación 7000. No se encontraron pisos validados independientes para V/R/H/D; no se inventaron.
- **Despacho y feedback:** se añadieron el scanner idempotente de ciclos explícitamente autorizados y el reconciliador que verifica la firma y el digest antes de escribir `verify` y `feedback`. Los tests integrados verifican el ciclo sintético completo y el no-reenvío al repetir el escaneo. Esto no prueba impacto comercial ni genera transacciones reales.
- **Producción comprobada al cierre:** `/healthz` respondió `{"status":"ok","service":"chalamandra-agent-engine","execution_enabled":false}`. El contenedor `chalamandra-api` sigue `running / healthy` con imagen `chalamandra-agent-engine:backup-pre-e6d67db`. No se recreó ni reinició por este trabajo.
- **Bloqueos de activación confirmados:** `CHALAMANDRA_CATEDRALX_JWT_SECRET`, `CHALAMANDRA_VERIFIER_PUBLIC_KEY` y `CHALAMANDRA_VERIFIER_ID` no están presentes en el entorno del contenedor. Los timers `chalamandra-feedback-reconcile.timer` y `chalamandra-catedralx-dispatch.timer` aparecen `not-found`; las unidades de repositorio son plantillas candidatas, no servicios activos.
- **Estado de repositorios:** hay cambios locales no comprometidos en ambos checkouts, junto con archivos nuevos. No se ejecutaron `git reset`, commit, push, publicación ni promoción de imagen. Mantener todas las modificaciones hasta revisión y aprobación explícita.

**Conclusión operativa:** la integración local y sus pruebas pasan; el servicio de producción sigue en modo no ejecutor y no está activado el despacho automatizado. Para avanzar sin abrir un riesgo de producción, el siguiente paso es provisionar identidades y secretos fuera del repositorio, elegir el ledger de ciclos autorizado y ejecutar una prueba de aceptación aislada antes de instalar los timers o promover una imagen.

## Evidencia de cierre parcial — 2026-10-28

- Se capturó la línea base en /home/azureuser/.local/state/chalamandra/release-audit/lineage-baseline-20261028T130430Z.json (SHA-256 e7e2b6d4b26109a686d14b08f216bb7f6bd79161c1f8355b1c13b3d140043666). No contiene valores de secretos.
- Se construyó, sin promover, la imagen chalamandra-agent-engine:reconciled-candidate-20261028-1305, image ID sha256:305bc892049e82706724860d61d4c823eb3c8b949a5d6e503915375049d2c7cf, a partir del base image ID sha256:3cbf4831dafcac7f832178cd2f6fd32d1928d6f696080f099367afef982f99ad. Las etiquetas de la imagen fijan los HEAD de Agents (4538cc0809fa028b470a2c7f584f5feac41c1228) y CatedralX (e6d67dbe3f6faad95a5c07286ce593b2777e6498) y el hash del contexto d049a3427c1a55a82cfc88e7ddb1b5d8d0bb5b3739dbc3e6b3015934aa3d7a28.
- El canary con el checkout local y datos sintéticos test-cycle-001 pasó el circuito completo: despacho HTTP 202; candidato en espera de aceptación; aceptación firmada HTTP 201; entrega HTTP 200; run final accepted; firma Ed25519 verificada desde el registro persistido con identidad fijada; continuidad de trace ID W3C; y ledger completo measure → evaluate → propose → authorize → verify → feedback. Nueve registros de traza persistidos. No se habilitaron llamadas de modelos ni se crearon/ejecutaron órdenes. Evidencia en /home/azureuser/.local/state/chalamandra/canaries/test-cycle-001-20261028T132215Z-58245f/summary.json (SHA-256 6b525f7008813f6f3477bb2705ecaf02946981f1cfb64542121f6e38275204e2).
- La imagen candidata pasó una prueba aislada de arranque: /healthz HTTP 200, API healthy e imports de api.server, api.catedralx_feedback y api.trace_store. El circuito end-to-end completo dentro de la imagen candidata aún no está verificado; no se debe inferirlo a partir de la prueba del checkout local.
- La producción chalamandra-api sigue en chalamandra-agent-engine:backup-pre-e6d67db / sha256:3cbf4831dafcac7f832178cd2f6fd32d1928d6f696080f099367afef982f99ad, healthy, cero reinicios y execution_enabled=false. No se promovió la candidata, no se habilitó ningún timer, no hubo commit ni push.
- También se observó mediante lectura un contenedor separado chalamandra-api-canary en 127.0.0.1:18767, imagen chalamandra-agent-engine:prod-e6d67db, healthy, con variables de servicio/verificador presentes por nombre. No se modificó ni se utilizaron sus secretos o su volumen como parte de esta prueba. Debe reconciliarse con el operador antes de decidir si sigue siendo necesario.
- Informe de evidencia sin secretos: /home/azureuser/.local/state/chalamandra/release-audit/release-evidence-20261028-132921.json (SHA-256 ebe03a9c603abf35b81024a8b5bc45f1b403b6390bf2787f7615a0cdb90c2d62).

Siguiente puerta de liberación: repetir los tres flujos contra la imagen candidata, con estado aislado, incluido el flujo completo de aceptación/feedback, y después acordar la reconciliación del contenedor chalamandra-api-canary. No habilitar timer, promoción o conexión comercial antes de esa aceptación.

## Última pasada de validación — 2026-10-28 13:33 UTC

- Suite completa Agents en su venv y con CATEDRALX_PATH explícito: **200 passed in 26.62s**.
- Suite completa CatedralX en su venv con PYTHONPATH=elite: **310 passed in 0.67s**.
- Ruff y git diff --check en ambos repositorios: **passed**.
- Se compararon 16 archivos críticos entre el checkout actual, el manifiesto del contexto congelado y la candidata; **16/16 hashes coinciden**.
- La candidata conserva image ID sha256:305bc892049e82706724860d61d4c823eb3c8b949a5d6e503915375049d2c7cf y contexto d049a3427c1a55a82cfc88e7ddb1b5d8d0bb5b3739dbc3e6b3015934aa3d7a28.
- Evidencia final: /home/azureuser/.local/state/chalamandra/release-audit/release-evidence-final-20261028T133359Z.json (SHA-256 1c108140b9334da5effb8b0178522ec1e854501dd68d9d6a21462b152fb83f5d).
- La prueba end-to-end completa de test-cycle-001 pasó usando el checkout local; la candidata pasó solo health/import smoke y comparación de hashes. Falta ejecutar el circuito completo dentro de la candidata. Por eso la liberación sigue bloqueada.

## Cierre E2E dentro de la imagen candidata — 2026-10-28

Se completó el ciclo sintético test-cycle-001 dentro de chalamandra-agent-engine:reconciled-candidate-20261028-1305, con un volumen nuevo y credenciales aleatorias efímeras. La API recibió únicamente la clave pública y el identificador del verificador; la semilla privada estuvo en un archivo temporal separado y se entregó exclusivamente al proceso firmador one-shot con red desactivada.

- Imagen candidata: sha256:305bc892049e82706724860d61d4c823eb3c8b949a5d6e503915375049d2c7cf.
- Ciclo: e81c1b52-f4b7-4d67-b22b-e403cf6a4a3a.
- Despacho autorizado mediante elite/bin/dispatch_authorized_cycles.py: HTTP 202; task_id=c64a45b4-508e-4133-9832-d9c4c5efeaa1; run_id=616b4b91-08b8-41a0-ba16-9dbf65c3af7f; trace_id=f0a4a59bcc0944f7ade2ee5e3f140fbc.
- El worker devolvió candidato elegible 114ea05c-73a8-4929-9666-4aa4fd5dfa5e, vinculado al business_cycle_id del ledger. Se mantuvieron orders_created=false, orders_executed=false y las llamadas a modelos desactivadas.
- El firmador independiente generó firma Ed25519; el POST /v1/acceptance devolvió HTTP 201. La firma volvió a verificarse desde acceptance_store.jsonl, con identidad y digest de evidencia fijados. La semilla privada no estuvo presente en el entorno de la API.
- GET /v1/results/{candidate_id} devolvió HTTP 200 con delivery_status=accepted. Una lectura autenticada válida de /internal/v1/orchestration/runs/{run_id} devolvió HTTP 200 con status=accepted. Una lectura sin autenticación devolvió HTTP 401.
- El reconciliador escribió verify → feedback; el ledger terminó en measure → evaluate → propose → authorize → verify → feedback y marcó el ciclo completo.
- El log contiene 34 registros; seis pertenecen a los endpoints del flujo y comparten el mismo trace ID. Todos los traceparent presentes en esos registros cumplen el formato W3C.
- La segunda ejecución del scanner no creó otro despacho: el ciclo ya había avanzado a feedback y dejó de ser elegible.
- Pruebas de suites en los entornos virtuales: Agents 200 passed; CatedralX 310 passed. Ruff y git diff --check pasaron.
- Evidencia JSONL persistida (aceptación, candidatos, dispatches, ledger y trazas), con SHA-256 por archivo, en /home/azureuser/.local/state/chalamandra/release-audit/candidate-image-e2e-20261028T140700Z/.
- Informe consolidado: /home/azureuser/.local/state/chalamandra/release-audit/candidate-image-e2e-20261028T140700Z/candidate-image-e2e-summary.json; SHA-256 079856e5eaeab8da492a30d78be6b1db3b18c3d0ae2ba453f142db7cd0ce58e0.

El contenedor de prueba se detuvo y retiró tras exportar la evidencia; el volumen chalamandra_candidate_e2e_20261028_r1 se conserva para auditoría. No se habilitó timer, no se promovió la imagen, no se modificó la producción y no se hizo commit ni push. Las credenciales efímeras y el material privado temporal se eliminan al cerrar el canary.


## Corrección de binding tras promoción operativa — 2026-10-28 14:36 UTC

Durante la puesta en servicio de la candidata, `chalamandra-api` estaba saludable según el healthcheck interno, pero el host recibía `connection reset` en `127.0.0.1:8766`. La causa fue la precedencia de `CHALAMANDRA_API_HOST=127.0.0.1` sobre `API_BIND_HOST=0.0.0.0`: el proceso escuchaba en loopback dentro del contenedor bridge, mientras Docker intentaba publicar el puerto del contenedor.

Se corrigió el contenedor principal manteniendo la imagen candidata y el volumen persistente `chalamandra_prod_state`, con `CHALAMANDRA_API_HOST=0.0.0.0`, `ALLOW_CONTAINER_BIND=true`, `CHALAMANDRA_API_ENABLE_MODEL_CALLS=false` y publicación host limitada a `127.0.0.1:8766`.

- Verificación desde el host: `GET /healthz` → HTTP 200, `status=ok`, `execution_enabled=false`.
- Verificación de runtime: `CHALAMANDRA_API_ENABLE_MODEL_CALLS=false`; `CHALAMANDRA_ED25519_SEED` ausente; `0.0.0.0:8766` en la interfaz del contenedor.
- Estado del contenedor principal al verificar: healthy, cero reinicios, imagen `sha256:305bc892049e82706724860d61d4c823eb3c8b949a5d6e503915375049d2c7cf`.
- La etiqueta `prod-20261028-rollback` se corrigió para apuntar a la imagen previa preservada `sha256:3cbf4831dafcac7f832178cd2f6fd32d1928d6f696080f099367afef982f99ad` (`backup-pre-e6d67db`), no a la candidata.
- En la inspección se encontró además `decox-candidate-e2e-20261028-r1` todavía ejecutándose en `127.0.0.1:18768` y `agents-predeploy-verify-1793182996` en `127.0.0.1:18766`; no se modificaron en esta corrección. Reconciliar su propósito y estado antes de retirarlos.
- Las suites locales de 200 tests Agents y 310 CatedralX pasan según la pasada registrada arriba; los 3 tests invocados por el operador pasaron. La corrección del binding se verificó con el health endpoint de la instancia publicada, pero eso no certifica por sí solo todos los flujos ni autoriza timers o conexiones comerciales.
- El operador expuso credenciales de API/verificador/JWT en el chat. Tratar esos valores como comprometidos y rotarlos coordinando los consumidores; no volver a copiarlos en registros, salidas ni documentación.

Sin timer habilitado, sin commit/push y sin cambios al volumen persistente durante la corrección.
