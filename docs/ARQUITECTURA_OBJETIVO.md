# Arquitectura objetivo — Chalamandra Magistral DecoX

**Estado:** diseño objetivo con estado de implementación revisado en código  
**Fecha de diseño:** 2026-10-28; actualización del criterio operativo: 2026-11-11.
**Regla de evidencia:** código versionado no demuestra por sí solo que un servicio esté desplegado u operativo. La VM anterior está fuera del plan operativo; no se asume un host sustituto.

## 1. Principio rector: La Catedral

La Catedral coordina el ciclo de creación de valor: diagnosticar necesidades reales, crear y validar soluciones, capturar valor de forma sostenible, reinvertir en capacidades colectivas, medir y aprender, e institucionalizar lo que funcione. La rentabilidad es una dimensión, no el único objetivo; valor humano, distribución, resiliencia y calidad de evidencia también requieren indicadores explícitos.

## 2. Componentes canónicos y límites de autoridad

### CatedralX — núcleo analítico
Aplica reglas explícitas, cálculos reproducibles y criterios versionados; declara incertidumbre y límites. Los modelos no pueden sobrescribir sus reglas. Las etiquetas financieras `buy`, `sell` y `hold` son salidas analíticas, no órdenes.

### Malla de agentes — capacidades especializadas
Investiga, ejecuta herramientas permitidas, critica y busca contraevidencia. Un agente produce un candidato con evidencia; no puede convertir una afirmación propia en hecho validado ni autoaceptarla.

### Membrana API — frontera de acceso y entrega
Autentica, autoriza scopes, valida contratos y límites, controla idempotencia y entrega estado/resultados. HTTP 200/202 no equivale a aceptación epistemológica.

### Plano de evidencia y aceptación
Registra entradas, versiones, procedencia, contraevidencia, pruebas, digests y decisiones de aceptación. La aceptación debe proceder de un verificador independiente en permisos y custodia de claves.

### Sustrato de ejecución — plataforma y servicios
Sostiene procesos, almacenamiento, conectividad, secretos y observabilidad. Es independiente del núcleo analítico y puede cambiar sin alterar los contratos lógicos. No hay plataforma de ejecución actual confirmada en este repositorio. Un Dockerfile, compose o archivo systemd versionado no prueba que esté desplegado o activo.

## 3. Tres planos independientes

- **Control:** tarea, prioridad, permisos, deadline, criterios de éxito y condición de parada.
- **Evidencia:** observaciones, fuentes, hashes, versiones, supuestos, contradicciones, pruebas y resultados de verificación.
- **Entrega:** publicación solo cuando contrato, autorización y aceptación lo permiten.

La autoridad de control, la producción de evidencia y la aceptación final no deben residir en el mismo agente.

## 4. Tres modos de causalidad sobre el mismo núcleo

1. **Reactivo:** Usuario/producto → API → TaskBus → worker → CatedralX y herramientas de agentes → candidato/evidencia → verificador → API → consumidor.
2. **Retorno:** candidato/resultado → verificador independiente → evento autorizado → webhook/distribuidor → producto/usuario.
3. **Proactivo:** evento o condición → API interna autorizada → TaskBus → worker → evidencia/verificación → alerta/entrega.

La existencia de un endpoint que acepta disparadores no prueba que exista un scheduler desplegado. Los tres modos deben compartir IDs consistentes, trazabilidad, permisos, deduplicación, límites y condiciones de parada.

## 5. Contrato mínimo del ciclo

### Entrada
- ID de solicitud/clave de idempotencia, trace ID validado y versión de contrato.
- Objetivo, tipo de tarea y payload con esquema explícito.
- Fuentes y tiempos de observación, si proceden.
- Herramientas/permisos autorizados, deadline y criterios de éxito.

### Salida candidata
- `candidate_id`, ID de tarea, versión del motor/contrato y estado.
- Decisión analítica, métricas, evidencia estructurada y digests reproducibles.
- Procedencia, fecha, supuestos, contraevidencia, contradicciones y datos faltantes.
- Pruebas ejecutadas, límites y siguiente acción sugerida.

### Aceptación
La decisión debe referenciar el candidato y el digest exacto, criterios evaluados, razones/faltantes, identidad del verificador y fecha. La firma debe comprobarse con la clave pública correspondiente; la clave privada no debe estar en la API/worker que recibe candidatos.

## 6. Mapa inicial de repositorios

| Repositorio | Rol objetivo | Límite |
|---|---|---|
| `Chalamandra-Magistral-deco/CatedralX` | Núcleo analítico determinista y contratos. | No permitir que un LLM sustituya reglas ni ejecutar órdenes financieras. |
| `Chalamandra-Magistral-deco/chalamandra-agent-engine` | Agentes, API local, TaskBus, worker, stores y distribución. | Consume CatedralX; no debe concederse autoridad de aceptación al worker. |
| `Chalamandra-Magistral-deco/CHALAMANDRA-MAGISTRAL` | Portal institucional y captación. | El formulario/Worker externo no se considera conectado hasta probar entrega y recibo. |
| `Tricentric-Integration`, `SYSTEM_DECODE_MAGIS-v12.0-FLUX`, `INTERACTIVE-DECOX` | Productos web independientes. | Integrar como clientes solo cuando haya un caso de uso y contrato concreto. |
| `OMNI-CHALAMANDRA-decox`, `Chalamandra-Triada`, `CHMADEX-DIAL`, `Insightify-Chalamandra`, `Challamandra-Analisis-cognitivo`, `chalamandra-6-sombreros` | Productos/capacidades cognitivas especializadas. | El posible solapamiento funcional no justifica eliminar ni fusionar sin evaluar código, uso, despliegue, clientes y dependencias. |
| `Chalamandra-Magistral-Decodificadora`, `Pirinola-`, `Blueprint-Chalamandra---SRAP-Barrio-Edition` | Portafolio, experiencias de marca o prototipos. | Estado comercial y conexiones por verificar por separado. |
| `Bunker-magistral`, `CHALAMANDRA-S-BUNKER`, `Chalamandra-all`, `brand.kit`, `demo-repository` | Infraestructura, identidad, documentación o demo por clasificar con evidencia. | No tratarlos como núcleo canónico ni eliminarlos por su nombre. |

Esta clasificación es preliminar: se basa en metadatos, README y archivos accesibles. No prueba que todos los productos estén conectados entre sí.

## 7. Estado observado en el código (2026-10-28)

| Componente | Observación | Estado |
|---|---|---|
| CatedralX | Código determinista, `BIN/catedral` y pruebas presentes. | Suite local verificada el 2026-10-28: 337 passed; Ruff global aún reporta diagnósticos heredados por revisar. |
| TaskBus | SQLite, reserva e idempotencia presentes en `api/task_bus.py`. | Código presente; integración completa pendiente. |
| Worker | `api/worker_loop.py` invoca CatedralX; `chalamandra-worker.service` se observó activo en el checkout WIP el 2026-10-28. | El worker puede correr una revisión distinta a la imagen de API; controlar la compatibilidad de estado antes de promover. |
| Request flow | Rutas de runs/jobs, TaskBus SQLite, creación de candidatos y aceptación independiente existen en el checkout de trabajo. | Pruebas locales pasan; no declarar la imagen estable certificada por esos resultados únicamente. |
| Aceptación | El checkout de trabajo contiene `api/acceptance_store.py` con verificación Ed25519, clave pública y digest; el firmador está en `verifier/independent_acceptance_verifier.py`. | Código actual observado; la separación real de claves debe comprobarse por entorno y contenedor. |
| Distribución | `api/server.py` expone suscripciones y publicación interna; `subscription_store`, `webhook_dispatcher` y `distribution_store` implementan política SSRF, firma HMAC de webhook e idempotencia global/por suscriptor. | Código presente y pruebas de distribución; contrato OpenAPI actualizado de forma parcial el 2026-10-28. |
| Orquestación interna | Endpoints de runs y resultados presentes. | **Corrección P0 fusionada:** commit `aee4e114ecdc86d9ff8abade69e02799b500d90e` restaura `orchestration:read` y `tasks:complete`, usa `task_bus.get_run_tasks()` y pasa CI de pruebas, Ruff, mypy y smoke test de imagen. La operación real en VM sigue sin comprobarse. |
| Parser W3C | `api/trace_parser.py` está conectado a la API y a `webhook_dispatcher`; los registros HTTP se escriben mediante `api/trace_store.py` en la revisión de trabajo. | Código presente; verificar en la imagen concreta antes de liberar. |
| Modo proactivo | `elite/bin/dispatch_authorized_cycles.py` realiza un escaneo one-shot de ciclos elegibles y despacha por API autorizada. | No se confirmó timer periódico habilitado. |
| VM/API/túnel | API Docker en 127.0.0.1:8766 y worker systemd activos; API responde healthz 200. | API estable usa imagen rollback antigua; worker carga checkout WIP. DNS/túnel y tráfico externo no forman parte de esta verificación. |
| CI | No se verificó CI remoto del HEAD actual. Las suites locales se ejecutaron en la VM. | No declarar CI remoto verde sin evidencia del commit exacto. |

## 8. Regla de configuración segura

`CHALAMANDRA_API_ENABLE_MODEL_CALLS` permanece **deshabilitado por defecto**. No se cambia a `true` solo porque la arquitectura contemple agentes generativos.

Solo se habilita tras verificar autorización/scopes en todas las rutas, identidad de servicio separada, herramientas permitidas, límites de costos/deadlines, aceptación independiente, custodia de secretos, pruebas de la vertical slice, CI completo y política de red. Esta definición no modifica ni reinicia producción.

## 9. Criterios de aceptación antes de ampliar la arquitectura

1. Mismas entradas y versión producen la misma salida determinista en CatedralX.
2. API valida schemas, scopes, límites, idempotencia y estado antes de entregar resultados.
3. Worker no puede firmar ni aceptar sus propios candidatos.
4. Digest y firma detectan alteraciones; la clave privada del verificador está fuera del worker/API.
5. Los modos conservan trazas y mapeos únicos entre tarea, candidato, resultado y decisión.
6. Bloqueo, fallo e incertidumbre nunca se publican como aceptación.
7. Suite, Ruff, mypy, build y prueba de extremo a extremo pasan en el commit exacto.
8. Despliegue validado con evidencia de la VM; Vercel `READY` o archivos de configuración no prueban el flujo completo.

## Inventario del ecosistema y conexiones

La matriz de repositorios, vínculos evidenciados, limpiezas aplicadas y brechas de integración está en [`docs/INVENTARIO_ECOSISTEMA_Y_CONEXIONES.md`](docs/INVENTARIO_ECOSISTEMA_Y_CONEXIONES.md).


## Nota de vigencia — 2026-11-11

Este documento conserva el diseño objetivo fechado el 2026-10-28. Las menciones históricas a VM, systemd, túneles y runtime no describen un entorno actual. El estado verificable se mantiene en [ESTADO_PRODUCCION.md](ESTADO_PRODUCCION.md); la clasificación de snapshots está en [INDICE_DOCUMENTAL_Y_GOBIERNO.md](INDICE_DOCUMENTAL_Y_GOBIERNO.md).