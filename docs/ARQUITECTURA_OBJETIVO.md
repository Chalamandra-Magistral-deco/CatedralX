# Arquitectura objetivo — Chalamandra Magistral DecoX

**Estado:** diseño objetivo con estado de implementación revisado en código  
**Fecha de revisión de código:** 2026-10-26  
**Regla de evidencia:** código versionado no demuestra por sí solo que un servicio esté desplegado u operativo en la VM.

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

### Sustrato de ejecución — VM y servicios
Sostiene procesos, almacenamiento, conectividad, secretos y observabilidad. La VM no es una etapa lógica del análisis; su estado real exige inspección de procesos, systemd, variables, puertos, red y logs. Un archivo de servicio en Git no prueba que esté activo.

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

## 7. Estado observado en el código (2026-10-26)

| Componente | Observación | Estado |
|---|---|---|
| CatedralX | Código determinista, `BIN/catedral` y pruebas presentes. | Código presente; suite completa no ejecutada en esta revisión. |
| TaskBus | SQLite, reserva e idempotencia presentes en `api/task_bus.py`. | Código presente; integración completa pendiente. |
| Worker | `api/worker_loop.py` invoca CatedralX desde una ruta fija. | Código presente; proceso activo en la VM no verificado. |
| Request flow | Rutas de creación/consulta de trabajos y resultados presentes. | Parcial; no se demostró recorrido completo hasta resultado aceptado. |
| Aceptación | `acceptance_store` usa HMAC-SHA256 y compara el digest de evidencia. | Parcial; helper Ed25519 existe pero no está conectado al store. |
| Distribución | Store de suscripciones y webhook dispatcher presentes. | Parcial; no se confirmó `POST /v1/subscriptions`. |
| Orquestación interna | Endpoints de runs y resultados presentes. | **P0 en `main`:** GET de runs carece de scope y consulta funciones inexistentes; POST de resultados carece de autorización. Corrección propuesta en [PR #13](https://github.com/Chalamandra-Magistral-deco/chalamandra-agent-engine/pull/13), aún sin fusionar. |
| Parser W3C | `api/trace_parser.py` existe en agentes. | No integrado en `api/server.py`; requiere validar semántica W3C. |
| Modo proactivo | Endpoint de disparo interno presente. | Scheduler desplegado no confirmado. |
| VM/API/túnel | Unidad systemd para API versionada. | Estado real de procesos, entorno, red, DNS y logs no verificado. |
| CI | No hay resultado completo reciente confirmado para el commit actual. | No declarar verde. |

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
