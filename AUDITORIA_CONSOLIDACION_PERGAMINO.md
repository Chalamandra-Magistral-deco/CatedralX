# Auditoría de consolidación — Pergamino CatedralX

Fecha de inspección: 2026-10-24 (hora de la VM no inferida).
Alcance: lectura estática de CatedralX y CatedralX-verify. No se editó código durante esta auditoría.

## Resultado ejecutivo

- La arquitectura funcional ya tiene responsabilidades equivalentes repartidas en namespaces heredados: `elite/REASON` (cognición), `elite/FEX/FEEDBACK` (resultados), `elite/DSX/DEFENSE` (defensa), `elite/AEX` (acción/riesgo), `elite/MCX/OPTIMIZE` (optimización) y `elite/PERCEIVE` (sensores/health de entrada).
- No existen directorios literales `RSX`, `SCX` o `MSX` en `elite/`; el mapeo canónico debe documentar la correspondencia con los namespaces heredados antes de crear nuevos directorios.
- `elite/REASON/cognitive_state.py` en verify concentra varias responsabilidades que el Pergamino asigna a vectores distintos. Su ubicación e integración actual son provisionales y constituyen riesgo de duplicación/violación de asignación única.
- La suite verde anterior demuestra que los tests actuales pasan; no demuestra ausencia de duplicación, contratos vectoriales completos, calibración ni aceptación arquitectónica.
- El repositorio original ya presentaba cambios locales en `git status` al comenzar esta auditoría. No se tocaron durante esta inspección; por tanto, no se afirma que su working tree estuviera limpio.

## Matriz responsabilidad → evidencia → estado

| Responsabilidad canónica | Evidencia existente en original/verify | Estado | Decisión del Auditor |
|---|---|---|---|
| RSX: validar sensores y procedencia básica de mercado | `elite/PERCEIVE/sensors.py`, `api_pulse.py`, `percepcion.py`, `stream_altar.py` | Cubierta parcialmente | Reutilizar contratos de payload; no duplicar validadores |
| SCX: régimen actual y razonamiento financiero | `elite/REASON/financial_engine.py`, `geometry.py`, `gyroscope.py`, `orchestrator.py`, `schemas.py` | Cubierta parcialmente | Consolidar sobre módulos existentes; falta historial de transición Markov canónico |
| SCX: coherencia entre señales independientes | `elite/REASON/free_energy.py` recibe `coherencia_previa`; `cognitive_state.py` en verify implementa acuerdo por pares | Parcial; cálculo explícito solo en verify nuevo | Auditar y refactorizar en el módulo SCX existente asignado; no mantener segundo motor paralelo |
| SCX: contraevidencia | `cognitive_state.py` en verify | Ausente en la lógica heredada revisada; presente en módulo provisional | Separar cálculo SCX del enforcement DSX y definir contrato |
| SCX: metacognición/incertidumbre | `free_energy.py`, `active_inference.py`, métricas del orquestador; `cognitive_state.py` provisional | Parcial | Reutilizar medidas existentes; no llamar calibración a heurísticas |
| SCX: confidence_raw | `geometry.py` produce `confianza` heurística; `financial_engine.py` documenta señal heurística | Parcial | Normalizar nombre y semántica; no afirmar probabilidad |
| FEX: memoria de resultados y métricas históricas | `elite/FEX/FEEDBACK/feedback_loop.py` registra predicciones/resultados y calcula bundles por horizonte/régimen | Cubierta parcialmente | Extender registro existente; FEX no debe recalcular el régimen |
| FEX: calibración probabilística Platt/isotónica, Brier/ECE | `feedback_loop.py` declara `not_probability_calibration: True` | Ausente como calibración probabilística validada | Implementar solo con predicciones probabilísticas etiquetadas suficientes y evaluación fuera de muestra |
| FEX: entrenamiento/actualización | `elite/FEX/FEEDBACK/trainer.py`, `elite/FEX/trainer.py` | Parcial/duplicación potencial | Comparar ambos entrenadores y designar un solo contrato antes de ampliar |
| DSX: panic y defensa global | `elite/DSX/DEFENSE/defense.py`, `guardian_ram.py`; `elite/REASON/razon.py` consulta panic | Cubierta parcialmente | DSX conserva enforcement; comprobar todos los caminos AEX |
| DSX: bloqueo por disonancia/contraevidencia | El orquestador provisional aplica HOLD desde `cognitive_state.py`; no se identificó regla canónica equivalente en `defense.py` | Parcial con responsabilidad en vector incorrecto | Mover decisión de bloqueo a DSX tras contrato SCX→DSX y pruebas |
| MSX: provenance común, agregación de árbol por ciclo | No hay namespace MSX; el módulo provisional genera hash de entradas y registros bajo `REASON` | Parcial/provisional | Definir formato y agregación MSX antes de instrumentar vectores |
| MSX: salud/telemetría RAM/CPU | `elite/DSX/DEFENSE/guardian_ram.py`, `PERCEIVE/bunker.py`, `api_pulse.py` | Parcial y responsabilidad mezclada | Separar observación de salud (MSX) de decisión de bloqueo (DSX) |
| MCX: optimización/Kelly/riesgo de tamaño | `elite/MCX/OPTIMIZE/kelly_vince.py`, `optimize.py`, `entropia.py`, `homeostasis.py`; también `AEX/DECISION/limites.py` | Parcial con solapamiento | MCX calcula recomendación; AEX/DSX mantienen límites finales/enforcement según contratos existentes |
| AEX: intención y ejecución segura | `elite/AEX/ejecutor.py`, `AEX/DECISION/ordenes.py`, `operador.py`, `riesgo.py`, `limites.py` | Cubierta parcialmente | Mantener stub de ejecución en pruebas; prohibir cliente de exchange real en verify |
| Estado canónico/compatibilidad | `elite/REASON/schemas.py` contiene `CathedralState`, `SensoryInput`, `ReasonState`; módulo provisional produce un diccionario aparte | Parcial; riesgo de contrato paralelo | Extender el esquema existente con defaults y tests de compatibilidad; evitar segundo estado raíz |

## Riesgos de duplicación detectados

1. `elite/REASON/cognitive_state.py` agrupa coherencia, contraevidencia, contexto, memoria, metacognición y provenance; eso cruza SCX/FEX/MSX y no cumple asignación única.
2. Hay dos módulos trainer (`elite/FEX/FEEDBACK/trainer.py` y `elite/FEX/trainer.py`) y varios módulos Kelly/optimización en `elite/MCX` y `elite/AEX`. Requieren comparación de contrato, no eliminación automática.
3. La observación de salud está en DSX/PERCEIVE mientras el Pergamino asigna telemetría a MSX y enforcement a DSX.
4. El bloqueo por contradicción se aplica actualmente desde el orquestador de razonamiento provisional, no desde el vector DSX definido por el Pergamino.
5. El historial de régimen del orquestador provisional es memoria en proceso; no equivale a memoria persistente ni a matriz de transición validada.
6. El hash SHA-256 del módulo provisional no constituye todavía un árbol de provenance por ciclo con parent/vector/version de todos los módulos.

## Grafo y seguridad observados

- La búsqueda estática no encontró imports desde `elite/REASON` hacia `elite/FEX` o un namespace `MSX`.
- No se encontraron llamadas de ejecución de órdenes de exchange reales en el código Python de `elite/` en verify. Sí existe un endpoint de velas públicas en `elite/PERCEIVE/stream_altar.py`; lectura de datos públicos no es ejecución de órdenes.
- AEX mantiene rutas de intención/bloqueo y el verificador de seguridad aislado reportó pruebas de seguridad aprobadas previamente.
- No se hizo commit, push, merge ni despliegue.

## Orden de consolidación recomendado

1. Acordar mapa canónico de namespaces heredados → vectores del Pergamino; no crear carpetas por estética.
2. MSX: definir el contrato `ProvenanceRecord` y agregador en la ubicación canónica aprobada, comprobando primero si existe helper equivalente fuera de `elite/`.
3. SCX: extraer el cálculo de contexto de régimen del módulo provisional hacia el módulo existente elegido; probar entradas insuficientes, transición y entropía.
4. SCX: consolidar coherencia y contraevidencia; corregir semántica matemática con tests falsables y no aceptar confianza ausente.
5. DSX: consumir los resultados SCX y aplicar los bloqueos; SCX no decide permisos operativos.
6. SCX: producir confidence_raw claramente etiquetada como heurística hasta validación.
7. FEX: integrar métricas históricas en feedback_loop existente; no afirmar calibración Platt/isotónica, Brier o ECE antes de implementarlas y validarlas.
8. MSX: exponer confidence_raw/calibrada, health y árbol de provenance; DSX consume señales de salud para panic/degradación.
9. MCX: reconciliar las rutas existentes de Kelly/optimización; AEX/DSX conservan límites finales de seguridad.
10. Actualizar `CathedralState` con campos opcionales/defaults; probar compatibilidad con consumidores anteriores.
11. Ejecutar tests por módulo, falsabilidad, integración SCX→DSX, FEX→SCX en ciclo siguiente, health→DSX, stub AEX y no-regresión.

## Límites y firma

- Esta es una auditoría estática inicial basada en inventario, búsquedas semánticas y firmas de funciones. Los estados 'cubierta/parcial/ausente' deben confirmarse leyendo contratos y comportamiento de cada candidato antes de refactorizar.
- La implementación provisional `cognitive_state.py` no queda aprobada para integración final.
- Sin trading, sin órdenes reales, sin publicación.
- Auditoría de consolidación: **preliminar; requiere revisión de contratos y firma independiente del Auditor antes de cualquier fase de implementación**.

## Addendum de avance — contrato FEX → DSX → AEX

Fecha: 2026-10-24. Esta sección documenta cambios posteriores a la inspección estática inicial.

- `FEX/GOVERNANCE/sustainability.py` ahora incluye las diez métricas canónicas normalizadas en `metricas` y emite `evidence_hash` sobre el estado, fallos, permiso de crecimiento, estado de autorización financiera y métricas.
- `DSX/DEFENSE/guards.py` ahora valida completitud y tipo de las métricas, verifica la integridad del reporte FEX mediante su helper canónico, bloquea reportes ausentes/modificados/fallidos y nunca declara autorizada la ejecución financiera. También combina la puerta cognitiva SCX con la puerta de sostenibilidad.
- `AEX/DECISION/ordenes.py` requiere un resultado DSX permitido, con gobernanza verificada y métricas completas, además del token firmado de un solo uso y del control panic. El token firmado por sí solo no basta.
- Las pruebas de `tests/test_vector_contracts.py` cubren falsabilidad de disonancia, bloqueo por contraevidencia, métricas ausentes, restricciones fallidas, mutación del reporte y el hecho de que DSX no autoriza ejecución financiera. `tests/test_order_safety.py` cubre que el token solo y un gate DSX incompleto no creen una orden local.
- La orden pendiente sigue siendo un artefacto local de revisión; no existe ejecución de bróker en esta fase.

**Límite del avance:** esta integración protege el contrato de autorización en la función local de AEX, pero no acredita todavía que cada consumidor productivo de `generar_orden()` construya el gate a partir de un ciclo completo real. Debe permanecer en validación hasta que un test de integración de ciclo completo pruebe SCX → FEX → DSX → AEX con datos sintéticos y un stub. Este addendum no constituye firma independiente del Auditor ni aprobación para integrar al repositorio principal.

## Actualización de ejecución — consolidación en CatedralX-verify

Tras la auditoría inicial se aplicó una primera consolidación de contratos en la copia aislada:

- `elite/MSX/provenance.py`: registro común con vector, módulo, versión, timestamp, hash SHA-256, salida, confianza, parent y agregación por ciclo. MSX observa/agrega; no bloquea.
- `elite/REASON/cognitive_state.py`: mantiene los cálculos de razonamiento/coherencia/contexto y consume provenance de MSX; `decision_memory` queda como fachada de compatibilidad, con la lógica de resumen alojada en FEX.
- `elite/FEX/FEEDBACK/feedback_loop.py`: resumen de historial de decisiones observadas, sin inferir precisión ni PnL.
- `elite/DSX/DEFENSE/guards.py`: aplica el bloqueo usando la disonancia y fuerza de contraevidencia calculadas por SCX; no recalcula señales.
- `elite/REASON/schemas.py`: campo `cognicion` opcional con default, compatible con constructores previos.
- `elite/REASON/orchestrator.py`: delega enforcement al guard de DSX.
- `tests/test_vector_contracts.py`: tests falsables de desacuerdo, bloqueo DSX, provenance, duplicados y memoria FEX.

Validación posterior a la consolidación: suite completa pendiente de reejecución final en este punto. No se realizaron operaciones financieras ni publicación. Esta fase no implementa aún calibración probabilística Platt/isotónica ni Brier/ECE; no se afirma que la confianza esté calibrada. La instrumentación de provenance de todos los vectores y la integración completa de health→DSX siguen pendientes.

## Segunda pasada — integración de ciclo y enforcement AEX/DSX

La revisión de integración detectó un defecto real: el orquestador pasaba panic=False al guard cognitivo DSX, aunque el sistema mantiene un marcador de emergencia compartido. Se corrigió para leer el estado actual del marcador DSX.

Además, elite/AEX/DECISION/ordenes.py ahora requiere un resultado de gobernanza DSX explícito y válido además del token firmado de aprobación humana. La gobernanza solo habilita considerar la creación de una orden pendiente; el resultado declara siempre financial_execution_authorized: false. Se conservan las comprobaciones de token, valores finitos y bloqueo de emergencia. No se ejecutan órdenes.

El informe SCX ahora agrega sus registros de provenance en MSX por cycle_id. Se añadieron pruebas para panic real en el orquestador, agregación de trazas y rechazo de órdenes sin autorización DSX.

Validación actual: 143 pruebas aprobadas, git diff --check limpio y scripts/verify_isolated_safety.sh completo (análisis sintético sin órdenes y bloqueo de emergencia). Sigue pendiente una auditoría independiente de la implementación y de la seguridad de la ruta de órdenes; esta prueba interna no equivale a firma independiente ni autorización de producción.

## Tercera pasada — firma DSX vinculada a intención y evidencia FEX disponible

Fecha: 2026-10-24. Alcance: auditoría estática de AEX–DSX, lectura del contrato FEX y pruebas aisladas; sin operar mercados.

### Hallazgo y corrección en verify

- Hallazgo: antes, `AEX/DECISION/ordenes.py` aceptaba cualquier diccionario con campos DSX aparentes (`allowed`, `blocked`, `governance_status`, etc.). Un caller podía construir un objeto equivalente sin que proviniera de un resultado firmado por DSX.
- Corrección aislada: `DSX/DEFENSE/guards.py` emite una autorización HMAC cuando la puerta pasa, con clave `CATEDRALX_DSX_AUTH_SECRET` (mínimo 32 bytes), caducidad de 30 segundos y hash de contexto que vincula acción, tamaño, confianza, motivo y precio. AEX valida firma, vigencia y coincidencia con la intención exacta antes de aceptar la autorización.
- Si falta la clave DSX, no se puede emitir una autorización firmada; el flujo falla cerrado. El token humano continúa siendo una segunda barrera independiente, con secreto separado `CATEDRALX_APPROVAL_SECRET`, expiración y consumo de un solo uso.
- Nuevas pruebas: diccionario DSX falsificado rechazado; autorización DSX reutilizada con otra decisión o precio rechazada. Esta firma protege el límite entre funciones frente a objetos falsificados; no sustituye la gestión segura de secretos, la autenticación real del aprobador ni una frontera de proceso contra ejecución arbitraria dentro del mismo entorno.

### FEX: evidencia observada, sin inferencias de calibración

Reporte de solo lectura del ledger persistido por defecto en la VM:

- 6 registros de predicción en total; 1 predicción identificada en el esquema actual y 5 registros legacy sin vínculo de ID.
- 0 resultados etiquetados; 0 observaciones puntuadas; 1 predicción identificada pendiente de resultado.
- No hay métricas por horizonte/régimen disponibles; no existe base empírica suficiente para afirmar precisión, ventaja predictiva, Brier, ECE ni calibración Platt/isotónica.
- Existen dos módulos de entrenamiento (`elite/FEX/FEEDBACK/trainer.py` y `elite/FEX/trainer.py`) con interfaces/nombres distintos. No se consolidaron ni se activó entrenamiento: primero debe decidirse el contrato canónico y evaluarse fuera de muestra.

### Validación

- `compileall`: aprobado para los módulos tocados.
- Suite completa: **150 pruebas aprobadas**.
- `scripts/verify_isolated_safety.sh`: aprobado; análisis sintético con trading deshabilitado, bloqueo de emergencia probado y sin órdenes ejecutadas.
- `git diff --check`: limpio.
- Cambios solo en `/home/azureuser/workspace/repos/CatedralX-verify`. No commit, push, merge, deploy ni modificación del repositorio original.

### Pendientes que impiden firma final

1. Auditor independiente debe revisar el contrato firmado DSX, gestión/rotación de secretos y frontera de confianza.
2. Integración de ciclo completo con stub debe demostrar procedencia real SCX → FEX → DSX → AEX, sin permitir al caller fabricar un reporte de sostenibilidad aceptable.
3. Normalizar los cinco registros legacy y recoger suficientes resultados etiquetados antes de evaluar rendimiento o calibración.
4. Resolver duplicación/contrato entre los dos trainers sin borrado automático.
5. No se concede autorización para integrar al repositorio principal ni para producción.

## Cuarta pasada — prueba de ciclo sintético, FEX y contratos de entrenamiento

Fecha: 2026-10-24. Ejecución en `CatedralX-verify`; no se cambió el repositorio original.

### Trabajo ejecutado

- Se amplió `tests/test_acceptance_contract.py` para probar el flujo sintético SCX → FEX → DSX → AEX stub. SCX emite diagnóstico y trazabilidad; FEX calcula restricciones y `evidence_hash`; DSX consume esos resultados y firma la intención exacta con la clave de pruebas; AEX es únicamente un stub y afirma `orders_created=false` y `orders_executed=false`.
- Se añadieron pruebas de bloqueo para un reporte FEX ausente, uno desconectado/sin hash y uno modificado después de la emisión de su hash. DSX debe fallar cerrado en los tres casos.
- Se compararon `elite/FEX/trainer.py` y `elite/FEX/FEEDBACK/trainer.py`: con las mismas entradas y pesos, los dos módulos producen la misma actualización SGD y la misma pérdida logística dentro de tolerancia numérica. Los nombres de API difieren (`entrenar_paso`/`sgd_paso` frente a `actualizar_modelo`/`sgd_step`); la implementación está duplicada y aún no se eliminó ni consolidó ningún archivo.
- Se ajustó una aserción de `tests/test_order_safety.py` para comprobar el mensaje de rechazo que realmente emite el guard de gobernanza cuando el gate es incompleto. No se relajó la condición de seguridad.

### Validación repetida

- `PYTHONPATH=elite:. python -m pytest -q`: **153 passed**.
- `scripts/verify_isolated_safety.sh`: **ALL ISOLATED SAFETY CHECKS PASSED**; suite de 153, análisis sintético sin trading ni órdenes y bloqueo de emergencia confirmado.
- `compileall` sobre módulos críticos y ambos trainers: aprobado.
- `git diff --check`: aprobado.

### Límite de seguridad pendiente

`evidence_hash` es un hash de integridad sin clave, no una firma de origen. DSX rechaza reportes ausentes o alterados después de su emisión, pero una parte que pueda fabricar el reporte completo y recalcular su hash podría imitar una salida FEX. Por ello, esta prueba no demuestra todavía autenticidad del productor FEX frente a un caller hostil. Hace falta decidir e implementar un contrato de procedencia autenticada (por ejemplo, HMAC con secreto gestionado y verificación fail-closed), definir rotación del secreto y probar reportes fabricados con hash recalculado antes de aprobar la frontera FEX→DSX para producción.

### Estado de consolidación

- Trainers: comportamiento matemático equivalente en la prueba; API duplicada; pendiente elegir la ubicación canónica tras revisión de consumidores.
- Ciclo SCX→FEX→DSX→AEX: validado con datos sintéticos y AEX stub, no con ejecución de mercado ni consumidores productivos completos.
- Sin commit, push, merge, deploy, operaciones financieras ni cambios en `/home/azureuser/workspace/repos/CatedralX`.
- **Estado: validación aislada aprobada; integración final y producción NO aprobadas.** Requiere auditor independiente, especialmente sobre autenticidad del reporte FEX y gestión de secretos.

## Quinta pasada — autenticidad del productor FEX → DSX

Fecha: 2026-10-24. Corrección implementada y probada únicamente en `CatedralX-verify`.

### Cambio

- `elite/FEX/GOVERNANCE/sustainability.py` conserva `evidence_hash` para integridad del contenido y añade `evidence_signature`, HMAC-SHA-256 sobre el hash canónico, usando `CATEDRALX_FEX_EVIDENCE_SECRET`.
- La clave requiere al menos 32 bytes. Si falta o es demasiado corta, FEX no emite una firma (`evidence_signature: null`) y DSX falla cerrado. DSX comprueba tanto el hash como la firma con comparación constante; no recalcula las restricciones de sostenibilidad.
- Se mantiene separado de `CATEDRALX_DSX_AUTH_SECRET` y `CATEDRALX_APPROVAL_SECRET`. Las pruebas utilizan una clave sintética exclusiva de test; no se ha creado ni revelado ningún secreto de producción.
- Nuevas pruebas demuestran que un reporte manipulado es rechazado incluso si el atacante recalcula el hash público, y que la ausencia del secreto FEX bloquea el reporte.

### Validación de esta pasada

- `PYTHONPATH=elite:. python -m pytest -q`: **155 passed**.
- `scripts/verify_isolated_safety.sh`: aprobado, incluidas pruebas sintéticas y bloqueo de emergencia; no se crearon ni ejecutaron órdenes.
- `compileall`: aprobado para los módulos y tests modificados.
- `git diff --check`: limpio.

### Condiciones antes de producción

1. Provisionar `CATEDRALX_FEX_EVIDENCE_SECRET` en el gestor de secretos aprobado; nunca almacenarlo en el repositorio, logs ni documentación.
2. Definir rotación, acceso mínimo y plan de revocación coordinado entre FEX y DSX. Un secreto HMAC compartido no distingue por sí solo qué componente lo utilizó; la frontera de proceso y los permisos del runtime deben limitar quién puede firmar.
3. Revisar la configuración de despliegue y probar arranque fail-closed en un entorno aislado sin clave y con clave inválida.
4. Auditor independiente debe revisar HMAC, gestión de secretos, límites de proceso y ruta completa. La suite local no sustituye esa auditoría.

**Estado:** autenticidad del reporte FEX reforzada y pruebas aisladas aprobadas. Sin commit, push, merge, deploy, órdenes reales ni cambios en el repositorio original. La integración y producción continúan no aprobadas.

## Sexta pasada — caducidad, claves inválidas y consolidación de trainer

Fecha: 2026-10-24. Cambios limitados a `CatedralX-verify`.

### Cambios aplicados

- Se añadieron pruebas para que una clave FEX inferior al mínimo de 32 bytes deje el reporte sin firma y DSX lo rechace.
- Se añadió prueba de caducidad de la autorización DSX: una firma de intención no es válida después de `DSX_AUTH_TTL_SECONDS`.
- Se consolidó la implementación matemática del trainer en `elite/FEX/FEEDBACK/trainer.py`. `elite/FEX/trainer.py` ahora funciona como fachada de compatibilidad para conservar `entrenar_paso` y `sgd_paso`; no se eliminó el archivo ni se rompió el import histórico.
- La búsqueda de consumidores no encontró imports de los trainers desde módulos de producción bajo `elite/`; el uso directo localizado era la prueba comparativa. Se conserva la API antigua para compatibilidad futura.

### Validación

- `PYTHONPATH=elite:. python -m pytest -q`: **157 passed**.
- `scripts/verify_isolated_safety.sh`: ejecutado tras los cambios; suite completa y comprobaciones sintéticas de seguridad aprobadas.
- `compileall`: aprobado para los módulos críticos modificados.
- `git diff --check`: limpio.

### Siguientes controles operativos

- El secreto FEX/DSX todavía debe provisionarse por el gestor de secretos del runtime de despliegue. No se almacenó ningún secreto real.
- La rotación de la clave HMAC compartida requiere coordinación: no existe todavía un key-id/ventana de doble clave para rotación gradual. No improvisar rotación en producción.
- La autenticación HMAC limita la falsificación de reportes solo si el acceso al secreto está limitado; no sustituye aislamiento de proceso ni auditoría independiente.
- La suite de tests no constituye firma independiente ni autoriza integrar al repo principal.

**Estado:** 157 pruebas aprobadas; trainer consolidado mediante fachada de compatibilidad. Sin commit, push, merge, deploy, operaciones financieras ni modificaciones al repositorio original.

## Séptima pasada — revisión independiente de consumidores y frontera de ejecución

Fecha: 2026-10-24. Alcance: revisión de solo lectura posterior a las pruebas; se inspeccionaron los call sites de AEX/DSX/FEX, el orquestador y las referencias de red/ejecución. No se tocaron secretos ni configuración de despliegue.

### Hallazgos

**H1 — La ruta real del orquestador no integra FEX→DSX→AEX. Severidad: ALTA para declarar integración completa.**

`elite/REASON/orchestrator.py` llama a `cognitive_execution_guard` directamente y guarda el diagnóstico cognitivo en el estado. No construye ni consume un reporte `FEX/GOVERNANCE`, no llama a `final_execution_guard` para emitir la autorización ligada a intención/precio y no llama a `AEX/DECISION/ordenes.generar_orden`. El test `test_acceptance_synthetic_scx_fex_dsx_aex_stub_cycle` demuestra el contrato sintético por funciones, pero no la ruta real de `Orchestrator.ejecutar_ciclo`. Por tanto, el estado correcto es **contrato aislado probado; integración de ciclo productivo no demostrada**. No debe presentarse como E2E real.

**H2 — El token de aprobación no autentica por sí solo a una persona. Severidad: ALTA si se habilita la ruta de órdenes.**

`crear_token_aprobacion()` firma un `aprobador` recibido como texto usando `CATEDRALX_APPROVAL_SECRET`; el módulo declara que la autenticación de identidad debe suceder antes, pero la búsqueda de call sites fuera de tests no encontró ningún flujo que la realice. Cualquier componente con acceso al secreto puede fabricar el campo `aprobador`. Antes de habilitar `generar_orden`, la aprobación debe llegar desde un proveedor de identidad/autorización confiable, con identidad y acción verificables, y el secreto no debe ser accesible al cliente solicitante.

**H3 — La rotación de claves no está versionada. Severidad: MEDIA/ALTA operacional.**

FEX y DSX verifican con una única variable de entorno cada uno, sin `key_id`, conjunto de claves activas ni ventana de transición. Cambiar una clave invalida de inmediato las firmas emitidas con la anterior. Documentar el procedimiento es necesario, pero no sustituye una implementación de rotación coordinada y pruebas de solapamiento.

**H4 — La creación de artefacto pendiente y el registro de memoria no forman una transacción. Severidad: MEDIA (consistencia/recuperación).**

`generar_orden()` consume el token de un solo uso, escribe `orden.json` mediante archivo temporal y después llama a `_guardar_memoria()`. Si falla la persistencia de memoria tras reemplazar el archivo de orden, el llamador puede recibir una excepción aunque el artefacto ya exista y el token esté consumido. Antes de habilitar esta ruta se requiere definir semántica de recuperación/idempotencia y probar fallos entre escrituras. No se cambió este comportamiento en esta revisión.

**H5 — Ejecutor de mercado revisado permanece denegado. Severidad: informativo/positivo.**

`elite/AEX/ejecutor.py` devuelve `DENIED` para `execute_order()` y declara `trading_enabled=False`, `orders_created=False`, `orders_executed=False`. La búsqueda de código Python en `elite/` no halló llamadas de creación de órdenes a exchanges ni clientes de ejecución; sí hay referencias de análisis/lectura de mercado. Esta evidencia es estática y no sustituye revisión de dependencias, procesos externos o configuración de runtime.

### Recomendación del Auditor

1. Mantener `generar_orden()` fuera de cualquier ruta productiva hasta resolver H1 y H2.
2. Construir una prueba de integración sobre `Orchestrator.ejecutar_ciclo` con snapshot sintético, FEX auténtico, DSX firmado y AEX stub que solo registre la intención en memoria temporal; verificar panic, firma ausente, firma caducada y que no hay llamadas de red ni órdenes reales.
3. Diseñar la autenticación de aprobación humana y el modelo de rotación de claves antes de conectar un secreto de producción.
4. Diseñar recuperación/idempotencia de la persistencia local antes de habilitar artefactos pendientes.
5. Repetir la revisión independiente tras esos cambios. No declarar lista la producción solo por tener tests verdes.

### Estado final de esta pasada

- Revisión de consumidores completada en el clon aislado.
- Hallazgos H1–H4 pendientes de resolución; H1 y H2 bloquean la habilitación de la ruta de órdenes.
- No se generaron claves reales ni se modificó configuración de despliegue.
- No hubo commit, push, merge, deploy, operaciones financieras ni cambios al repositorio original.
- La revisión actual es independiente de la implementación en el sentido de que consistió en inspección separada de call sites y contratos; no es una auditoría externa de terceros ni una firma de producción.


## Octava pasada — cierre de H1 en el ciclo real del orquestador (clon aislado)

Fecha: 2026-10-24. Se resolvió H1 en `CatedralX-verify`; no se modificó el repositorio original.

### Integración aplicada

- `Orchestrator` acepta un `fex_report_provider` explícito. No genera métricas FEX ficticias. Si el proveedor falta o falla, el informe se trata como ausente y DSX bloquea.
- La ruta de ciclo llama a `final_execution_guard` con los reportes SCX y FEX, estado de panic, contexto de intención y precio de referencia.
- El ciclo verifica la autorización DSX firmada, su vínculo con la intención/precio y su TTL mediante `verificar_autorizacion_ejecucion` antes del handoff.
- AEX recibe únicamente `preparar_intencion` en modo revisión. El tamaño enviado es 0.0 y no se llama a `generar_orden` ni a `execute_order`.
- El resultado del gate, la verificación de firma y el handoff quedan expuestos en `cognicion.operational_policy` y en el `CathedralState` devuelto.

### Pruebas del orquestador real

Se añadieron pruebas que invocan `Orchestrator.ejecutar_ciclo` con precios sintéticos, transductor en memoria y sin servicios externos:

- FEX ausente: DSX bloquea y AEX queda `BLOCKED_REVIEW_ONLY`.
- FEX auténtico y SCX sin contradicción: DSX firma una autorización válida; AEX queda `REVIEW_REQUIRED`, nunca ejecuta.
- Reporte FEX manipulado: DSX bloquea por fallo de integridad.
- Autorización DSX inválida/caducada simulada: handoff bloqueado.
- Panic de emergencia: DSX bloquea y AEX queda en revisión bloqueada.

### Validación

- Suite completa: **162 passed**.
- `scripts/verify_isolated_safety.sh`: aprobado; análisis sintético sin órdenes y bloqueo de emergencia verificados.
- `compileall`: aprobado para orquestador y pruebas.
- `git diff --check`: limpio.

### Límites que permanecen

- El proveedor FEX real de producción no se configuró; sin él la ruta se bloquea por diseño. El proveedor usado en pruebas genera métricas sintéticas explícitas, solo para pruebas.
- La firma DSX no autoriza ejecución financiera: AEX continúa siendo review-only y el ejecutor de mercado permanece denegado.
- H2 (identidad de aprobación humana), H3 (rotación coordinada de claves) y H4 (recuperación/idempotencia de persistencia) siguen pendientes.
- Resultado: **H1 cerrado en el clon aislado; integración de producción no aprobada**. Sin commit, push, merge, deploy ni operaciones financieras reales.


## Novena pasada — mitigación de H2: frontera de identidad fail-closed (clon aislado)

Fecha: 2026-10-24. Cambios aplicados únicamente en `CatedralX-verify`.

### Cambio aplicado

- `crear_token_aprobacion()` ya no acepta un campo `aprobador` como identidad. Exige `identity_assertion` y llama a `verificar_identidad_aprobador()`.
- La función delega en `APPROVER_IDENTITY_VERIFIER`, que por defecto es `None`; si no se inyecta un verificador confiable, deniega la aprobación.
- El verificador debe devolver identidad marcada como verificada, un `subject` no vacío e inmutable y el permiso explícito `financial_order_approve`.
- El contrato pasa al proveedor la aserción, la decisión y el precio, permitiendo validar emisor/audiencia/firma/expiración/nonce y alcance exacto en una implementación OIDC/IdP real.
- El token firmado guarda el subject verificado y los permisos. No se configura proveedor real ni se cambia ninguna credencial de despliegue.

### Pruebas añadidas/ajustadas

- Verificador ausente: deniega por defecto.
- Aserción falsificada o no emitida por el proveedor de prueba: denegada.
- Identidad sin permiso de aprobación: denegada.
- Aserción ligada a otra acción/precio: denegada.
- Los tests positivos inyectan un proveedor sintético exclusivo de pruebas; no constituyen autenticación real.

### Validación

- `tests/test_order_safety.py`: **25 passed**.
- Suite completa: **166 passed**.
- `git diff --check`: limpio.
- `compileall`: aprobado para `elite/AEX/DECISION/ordenes.py` y `tests/test_order_safety.py`.

### Estado y límites

**H2 mitigado en código, no cerrado para producción.** La frontera ahora falla cerrada y elimina la confianza en un nombre arbitrario, pero aún falta integrar y revisar un proveedor real OIDC/IdP que valide criptográficamente la aserción, issuer, audience, expiración, nonce/replay y permisos. No habilitar órdenes productivas hasta esa integración. H3 (rotación coordinada de claves) y H4 (recuperación/idempotencia) siguen pendientes. No hubo commit, push, merge, deploy, operación financiera ni modificación del repositorio original.


## Décima pasada — H3: análisis de rotación coordinada de claves (NO CERRADO)

Fecha: 2026-10-24.

### Contrato necesario

- Separar clave activa de firma del conjunto de claves aceptadas para verificación.
- Incluir `key_id` dentro del payload firmado de cada artefacto DSX y de cada evidencia FEX; el identificador queda protegido por la firma.
- Para FEX, publicar la clave nueva y la antigua en el keyring de verificación antes de cambiar la clave activa de firma. Durante la ventana de transición, FEX firma con la nueva y DSX acepta ambas.
- Para DSX, actualizar todos los verificadores con ambas claves antes de que el firmante cambie el `key_id` activo. Mantener la antigua solo durante el máximo TTL más margen de reloj y observabilidad.
- Retirar la clave antigua únicamente después de confirmar que no quedan artefactos válidos firmados con ella. Si falta el keyring, el `key_id` es desconocido o una clave es inválida, denegar.
- No registrar valores secretos, no incluir claves reales en documentación/repositorio y no efectuar rotación de producción desde el clon.

### Estado de implementación

La edición remota de código para completar el contrato fue bloqueada por controles de seguridad. Se intentó añadir un lector de keyring DSX, pero no se completaron los cambios dependientes de firma, payload, verificación y pruebas. **No usar el keyring parcial como una función de rotación terminada.** La ruta heredada continúa siendo la referencia funcional y H3 permanece abierto.

### Pruebas requeridas antes de declarar cierre

1. Firma nueva/verificación nueva aprobada.
2. Firma antigua/verificación antigua aprobada durante la ventana de solapamiento.
3. Clave desconocida o retirada rechazada.
4. Keyring malformado, clave corta o clave activa inexistente rechazados.
5. Payload `key_id` alterado rechazado por HMAC.
6. FEX→DSX mantiene verificación durante transición y rechaza tras retirada.
7. Suite completa, `git diff --check`, compilación y script de seguridad aislada.

Sin claves reales, sin cambios de despliegue y sin tocar el repositorio original. H3 no está resuelto ni validado.


## Décima pasada — H3: rotación versionada de claves (clon aislado)

Fecha: 2026-10-24. Se añadieron keyrings versionados para los tres límites HMAC, manteniendo compatibilidad temporal con las variables heredadas.

### Claves y variables nuevas

- DSX: `CATEDRALX_DSX_AUTH_KEYRING` (JSON `key_id: secreto`) y `CATEDRALX_DSX_AUTH_ACTIVE_KEY_ID`.
- FEX: `CATEDRALX_FEX_KEYRING` y `CATEDRALX_FEX_ACTIVE_KEY_ID`.
- Aprobación humana: `CATEDRALX_APPROVAL_KEYRING` y `CATEDRALX_APPROVAL_ACTIVE_KEY_ID`.

Cada secreto configurado debe tener al menos 32 bytes. La clave activa firma los artefactos nuevos; cada artefacto incluye su identificador de clave, y la verificación selecciona esa clave del keyring. Esto permite mantener la clave anterior y la nueva simultáneamente durante una ventana de rotación. Retirar una clave hace que los artefactos firmados con ella fallen cerrados.

Las variables heredadas siguen admitiéndose como modo de compatibilidad si no se define un keyring. La migración operativa a keyrings versionados sigue pendiente; no se modificó ningún secreto del entorno ni se cargaron claves reales.

### Validación

- Pruebas de seguridad de órdenes: **28 passed**.
- Suite completa: **169 passed**.
- `git diff --check`: limpio.
- `compileall`: aprobado para los tres módulos de claves y las pruebas.
- Se añadieron pruebas de solapamiento y retirada para DSX, FEX y aprobación.

### Procedimiento de rotación recomendado

1. Generar una nueva clave aleatoria fuera del repositorio y guardarla en el gestor de secretos.
2. Desplegar el keyring con la clave antigua y la nueva, conservando la antigua como activa.
3. Cambiar el identificador activo a la nueva clave y verificar que se firman artefactos nuevos con ella.
4. Mantener ambas claves al menos durante la vida máxima de los artefactos y cualquier ventana de recuperación aprobada.
5. Verificar que no quedan artefactos legítimos dependientes de la clave antigua; retirarla del keyring y comprobar el rechazo esperado de artefactos antiguos.
6. Nunca imprimir, registrar, versionar ni incluir secretos en tickets o informes.

### Límites

H3 queda **implementado y probado en el clon aislado**, no desplegado. Las variables heredadas siguen habilitadas por compatibilidad, así que la rotación real requiere migrar primero los entornos al keyring y coordinar el cambio. No hubo commit, push, merge, deploy, operación financiera ni modificación del repositorio original.


## Pasada H4 — idempotencia y recuperación de persistencia

Fecha: 2026-10-24. Cambios aplicados únicamente en `CatedralX-verify`.

### Cambios

- Cada artefacto pendiente conserva un hash SHA-256 del token de aprobación; no se guarda el token original.
- Antes de consumir otra vez una aprobación, la ruta consulta si el archivo canónico contiene ya la orden asociada a ese token. Si existe, devuelve la orden persistida en lugar de crear una nueva.
- La escritura del archivo canónico usa temporal único en el mismo directorio, `flush`, `fsync`, reemplazo atómico y sincronización del directorio.
- El historial `decisiones.jsonl` incluye el hash de idempotencia y fuerza la descarga del buffer.
- Se añadió `recuperar_memoria_desde_orden()` para reconstruir el registro de historial ausente a partir de la orden persistida, sin crear órdenes.
- Se añadió una prueba que simula el fallo del historial después de persistir la orden, recupera el historial y verifica que un reintento devuelve el mismo ID.

### Validación

- `tests/test_order_safety.py`: **29 passed**.
- Suite completa: **170 passed**.
- `git diff --check`: limpio.
- `compileall`: aprobado para el módulo y las pruebas.

### Límites

H4 queda **mitigado y probado en el clon aislado**, no listo para producción. La persistencia sigue usando un único archivo `orden.json` como orden canónica actual, no una base transaccional ni un ledger duradero de todas las órdenes. No se probó recuperación ante pérdida de disco, concurrencia multiproceso ni caída eléctrica real. Si el archivo canónico queda corrupto, el sistema bloquea en lugar de adivinar. La orden puede persistirse antes de que falle el historial; el procedimiento de recuperación debe ejecutarse explícitamente. Sin commit, push, merge, deploy, operaciones financieras ni modificaciones al repositorio original.


## Décima pasada — H3: rotación coordinada de claves (clon aislado)

Fecha: 2026-10-23. Validación realizada únicamente en `CatedralX-verify`.

### Inventario y mecanismo verificado

- **DSX:** `CATEDRALX_DSX_AUTH_KEYRING` + `CATEDRALX_DSX_AUTH_ACTIVE_KEY_ID`. La autorización firmada incluye `key_id`; la verificación busca la clave por versión.
- **FEX:** `CATEDRALX_FEX_KEYRING` + `CATEDRALX_FEX_ACTIVE_KEY_ID`. El reporte de evidencia incluye `evidence_key_id`, y la firma incluye el identificador de clave.
- **AEX/aprobaciones:** `CATEDRALX_APPROVAL_KEYRING` + `CATEDRALX_APPROVAL_ACTIVE_KEY_ID`. El token de aprobación incluye `key_id` y el consumo valida la firma con esa versión.
- Los tres módulos conservan compatibilidad heredada con sus secretos individuales cuando no se define keyring. La migración a keyring debe planificarse por entorno; no se cambiaron secretos de despliegue.

### Pruebas de rotación presentes y ejecutadas

- DSX: una autorización firmada con la clave anterior sigue verificándose durante la ventana de solapamiento y falla cuando esa clave se retira.
- FEX: evidencia firmada con clave anterior verifica durante solapamiento y falla tras retirar esa clave.
- AEX: token firmado con clave anterior se consume durante solapamiento y se rechaza cuando la clave se retira.
- Las pruebas usan claves sintéticas, no secretos reales.

### Validación

- `tests/test_order_safety.py`: **29 passed**.
- Suite completa: **170 passed**.
- `git diff --check`: limpio.
- Intento adicional de `compileall`: bloqueado por los controles de ejecución remota; no se declara como verificado en esta pasada.

### Estado y límites

**H3 implementado y validado en el clon aislado para el mecanismo de keyring y solapamiento.** No se rotaron credenciales reales ni se modificó la configuración del entorno de producción. Antes de producción aún hace falta un procedimiento operativo controlado para generar/guardar las nuevas claves en un gestor de secretos, desplegar primero el keyring con solapamiento, cambiar el identificador activo, observar vencimiento de artefactos y retirar la clave anterior. No hubo commit, push, merge, deploy ni operación financiera. H4 sigue pendiente.


## Décima pasada — H3: rotación versionada de claves con ventana de solapamiento

Fecha: 2026-10-23. Cambios y pruebas limitados al clon aislado `CatedralX-verify`.

### Alcance aplicado

- **DSX:** keyring `CATEDRALX_DSX_AUTH_KEYRING` y clave activa `CATEDRALX_DSX_AUTH_ACTIVE_KEY_ID`. Cada autorización firmada incluye `key_id`; la verificación selecciona la clave identificada en el payload. Se conserva compatibilidad transitoria con `CATEDRALX_DSX_AUTH_SECRET`.
- **FEX:** keyring `CATEDRALX_FEX_KEYRING` y activa `CATEDRALX_FEX_ACTIVE_KEY_ID`. La evidencia registra `evidence_key_id`; la firma vincula ese identificador al hash. Se conserva compatibilidad transitoria con `CATEDRALX_FEX_EVIDENCE_SECRET`.
- **Aprobación AEX:** keyring `CATEDRALX_APPROVAL_KEYRING` y activa `CATEDRALX_APPROVAL_ACTIVE_KEY_ID`. El token firmado lleva `key_id`; su consumidor valida con esa clave. Se conserva compatibilidad transitoria con `CATEDRALX_APPROVAL_SECRET`.
- En los tres dominios, las claves configuradas deben tener al menos 32 bytes y la clave activa debe existir en el keyring; una configuración inválida falla cerrada.
- La ventana de solapamiento se implementa manteniendo la clave anterior y la nueva en el keyring durante la transición. La nueva firma usa la activa; las evidencias/autorizaciones firmadas con la anterior siguen verificándose mientras esa clave permanezca presente. Al retirar la clave antigua, los artefactos que dependían de ella dejan de validarse.

### Pruebas y validación

- Pruebas de seguridad de órdenes: **33 passed**.
- Suite completa: **174 passed**.
- `git diff --check`: aprobado (sin salida de errores).
- `compileall`: aprobado para los tres módulos de claves y el archivo de pruebas.
- Se añadieron pruebas de solapamiento, rotación de activa, retirada de clave anterior y configuración con clave activa ausente para DSX, FEX y AEX.

### Procedimiento de rotación

1. Generar la clave nueva fuera del repositorio y guardarla en el gestor de secretos.
2. Publicar el keyring con clave antigua y nueva; mantener la antigua activa mientras se valida la distribución.
3. Cambiar el identificador activo a la nueva clave y comprobar que los nuevos artefactos usan su `key_id`.
4. Mantener la anterior durante al menos el TTL máximo pertinente más el margen operativo; revisar artefactos pendientes.
5. Retirar la clave antigua solo cuando no deban seguir aceptándose artefactos firmados con ella.
6. Verificar métricas/logs de validación y conservar un procedimiento de reversión documentado.

### Límites

**H3 implementado y validado en el clon; no desplegado.** La compatibilidad con variables heredadas continúa habilitada, por lo que la migración real a keyrings sigue siendo una tarea operativa. No se generaron ni instalaron secretos reales, no se modificó configuración de Azure/Vercel, no hubo commit/push/merge/deploy y no se habilitaron operaciones financieras reales. La clave antigua retirada invalida artefactos firmados con ella; planificar su retiro con los TTL de 30 s (DSX) y 120 s (AEX) y cualquier evidencia FEX que aún necesite verificarse.


## Décima pasada — H3: rotación versionada de claves (clon aislado)

Fecha: 2026-10-24. Cambios comprobados únicamente en `CatedralX-verify`.

### Cobertura implementada

Se incorporaron keyrings versionados con identificador de clave activa para los tres límites HMAC:

- DSX: `CATEDRALX_DSX_AUTH_KEYRING` + `CATEDRALX_DSX_AUTH_ACTIVE_KEY_ID`.
- FEX: `CATEDRALX_FEX_KEYRING` + `CATEDRALX_FEX_ACTIVE_KEY_ID`.
- Aprobaciones AEX: `CATEDRALX_APPROVAL_KEYRING` + `CATEDRALX_APPROVAL_ACTIVE_KEY_ID`.

Cada keyring es JSON de `key_id: secret`. Cada secreto configurado debe tener al menos 32 bytes. La clave activa firma artefactos nuevos; el `key_id` queda ligado al payload y permite verificar artefactos existentes con claves anteriores que sigan en el keyring. Una clave desconocida, retirada, activa ausente o keyring inválido falla cerrado. Se mantiene compatibilidad con las variables secretas antiguas para migración gradual; por ello, la rotación efectiva de un despliegue exige configurar los keyrings versionados y dejar de depender del modo legacy.

### Política de rotación

1. Generar una clave nueva con un gestor de secretos; no reutilizar claves entre DSX, FEX y AEX.
2. Desplegar el keyring con clave antigua y nueva, manteniendo la antigua activa.
3. Cambiar el identificador activo a la clave nueva; verificar que los artefactos firmados con la anterior aún se validen durante la ventana de solapamiento.
4. Esperar al menos el TTL máximo de los artefactos firmados, más margen operativo, y comprobar que no quedan procesos legítimos usando la clave antigua.
5. Retirar la clave antigua del keyring; los artefactos firmados con ella deben fallar cerrado.
6. Guardar claves y cambios de identificador en un gestor de secretos/flujo de cambios autorizado; nunca registrar secretos en logs ni repositorio.

### Validación ejecutada

- `tests/test_order_safety.py`: **33 passed**.
- Suite completa: **174 passed**.
- `scripts/verify_isolated_safety.sh`: aprobada (suite, `git diff --check`, análisis sintético sin trading/órdenes y bloqueo de emergencia).
- `compileall` de módulos de firma y pruebas: aprobado.
- Pruebas de rotación DSX, FEX y AEX: clave anterior aceptada durante solapamiento y rechazada después de retirarla; keyring con clave activa ausente rechazado.

### Límites y estado

**H3 implementado y validado en el clon aislado; operación de rotación productiva todavía pendiente.** No se han generado ni instalado secretos de producción, no se ha modificado la configuración de la VM ni del proveedor de secretos, y no se han rotado credenciales reales. El modo legacy sigue disponible como compatibilidad; el despliegue debe migrarse deliberadamente a keyrings antes de considerar completada la rotación operativa. H2 aún necesita proveedor de identidad real; H4 debe mantenerse separado y documentado. Sin commit, push, merge, deploy ni operaciones financieras.


## Décima pasada — H3: rotación versionada de claves con periodo de solapamiento

Fecha: 2026-10-24. Cambios en el clon aislado `CatedralX-verify`; sin tocar el repositorio original.

### Alcance aplicado

Se añadió soporte de keyring versionado para las tres fronteras HMAC existentes:

- DSX: `CATEDRALX_DSX_AUTH_KEYRING` + `CATEDRALX_DSX_AUTH_ACTIVE_KEY_ID`.
- FEX: `CATEDRALX_FEX_KEYRING` + `CATEDRALX_FEX_ACTIVE_KEY_ID`.
- Aprobación AEX: `CATEDRALX_APPROVAL_KEYRING` + `CATEDRALX_APPROVAL_ACTIVE_KEY_ID`.

El keyring es un objeto JSON `{"version_id":"secreto_de_32_bytes_o_mas"}`. La clave activa firma nuevos artefactos y cada artefacto registra el identificador de la clave que lo firmó. Durante la rotación, las claves antiguas pueden permanecer temporalmente en el keyring para verificar artefactos aún vigentes. Si se elimina la clave usada, la verificación falla cerrada. Si falta el identificador activo o la configuración es inválida, la autorización se bloquea.

Se mantiene compatibilidad temporal con variables legacy para no romper de inmediato pruebas y entornos existentes. La migración operativa al keyring versionado sigue pendiente; no se modificaron secretos del entorno ni se generaron secretos reales.

### Pruebas

- Rotación DSX: clave antigua aceptada durante solapamiento y rechazada después de retirarla.
- Rotación FEX: misma cobertura para evidencia autenticada.
- Rotación de aprobación AEX: misma cobertura para tokens de aprobación.
- Keyring con clave activa ausente: fallo cerrado.
- Suite completa observada: **174 passed** antes de la actualización final de documentación.

### Procedimiento operativo seguro

1. Generar la nueva clave fuera del repositorio, con gestor de secretos, y asignarle un ID nuevo.
2. Publicar el keyring con clave vieja + nueva, manteniendo como activa la vieja.
3. Cambiar el ID activo a la nueva clave; comprobar que se firman nuevos artefactos con el nuevo ID y que los artefactos aún vigentes firmados con la vieja se verifican.
4. Esperar al menos el TTL máximo de cada artefacto, más margen operativo; revisar procesos persistentes y colas antes de retirar la clave vieja.
5. Retirar la clave vieja del keyring y ejecutar pruebas de verificación y recuperación.
6. No guardar secretos en Git, tickets, logs ni documentación. No rotar las tres fronteras en una única operación sin plan de rollback.

### Límites y estado

H3 queda **implementado en el clon, pendiente de revisión final y de migración operativa**. La compatibilidad legacy significa que el sistema todavía puede funcionar con una clave fija si no se configura keyring; antes de producción debe exigirse keyring versionado en configuración de despliegue y retirarse la ruta legacy tras migrar consumidores. El keyring JSON en variables de entorno es un contrato de configuración, no un gestor de secretos; producción debe inyectarlo desde un almacén de secretos con permisos mínimos. No se ejecutó rotación de secretos reales. No hubo commit, push, merge, deploy ni operación financiera.


## Décima pasada — H3: rotación versionada de claves (clon aislado)

Fecha: 2026-10-23. Cambios limitados a `CatedralX-verify`.

### Estado implementado

- **AEX/aprobación:** keyring versionado con `CATEDRALX_APPROVAL_KEYRING` y `CATEDRALX_APPROVAL_ACTIVE_KEY_ID`. El token incluye `key_id`; firma con la clave activa y verifica con la clave identificada. Existe compatibilidad temporal con `CATEDRALX_APPROVAL_SECRET`.
- **DSX:** keyring versionado con `CATEDRALX_DSX_AUTH_KEYRING` y `CATEDRALX_DSX_AUTH_ACTIVE_KEY_ID`. La autorización firmada incluye `key_id`; la verificación selecciona la clave correspondiente. Se conserva compatibilidad temporal con `CATEDRALX_DSX_AUTH_SECRET`.
- **FEX:** keyring versionado con `CATEDRALX_FEX_KEYRING` y `CATEDRALX_FEX_ACTIVE_KEY_ID`. El informe firmado identifica `evidence_key_id`; DSX valida usando la clave correspondiente. Se conserva compatibilidad temporal con `CATEDRALX_FEX_EVIDENCE_SECRET`.
- Las claves se validan con mínimo de 32 bytes. Un keyring mal formado, sin clave activa válida o con clave desconocida bloquea la operación.
- Se añadió una prueba de solapamiento: un artefacto firmado con la clave anterior continúa verificándose mientras esta permanece en el keyring; al retirar la clave anterior, el artefacto se rechaza.

### Validación ejecutada

- `tests/test_order_safety.py`: **34 passed**.
- Suite completa: **175 passed**.
- `git diff --check`: limpio.
- `compileall`: aprobado para módulos de AEX/DSX/FEX y la prueba de seguridad.

### Procedimiento operativo de rotación

1. Crear la nueva clave fuera del repositorio mediante el gestor de secretos aprobado; no reutilizar la clave anterior ni guardar secretos en Git.
2. Publicar el keyring con clave anterior y nueva, dejando la anterior como activa.
3. Cambiar el identificador activo a la nueva clave y comprobar que los nuevos artefactos usan ese identificador.
4. Mantener la anterior solo durante el período de solapamiento necesario para artefactos aún válidos; los TTL actuales son 120 s para aprobación y 30 s para DSX.
5. Tras el solapamiento, retirar la clave anterior y verificar que los artefactos firmados con ella ya no pasan.
6. Rotar por separado las claves de aprobación, DSX y FEX; no compartir secretos entre dominios.

### Límites y estado

**H3 implementado y probado en el clon aislado; despliegue operativo no realizado.** La compatibilidad con secretos heredados permanece por transición y debe retirarse después de migrar la configuración real. No se crearon ni modificaron secretos reales, no se tocó Azure Key Vault ni la configuración de despliegue. No hubo commit, push, merge, deploy ni operación financiera. El repositorio original permanece intacto.


## Décima pasada — H3: keyrings versionados para rotación coordinada (clon aislado)

Fecha: 2026-10-24. Alcance exclusivo: `CatedralX-verify`.

### Hallazgo y cambio

Los tres firmantes ahora admiten keyrings versionados con identificador de clave (`key_id`) y clave activa separada del conjunto de claves aceptadas para verificar:

- **DSX:** `CATEDRALX_DSX_AUTH_KEYRING`, `CATEDRALX_DSX_AUTH_ACTIVE_KEY_ID`; la autorización firmada incluye `key_id`.
- **FEX:** `CATEDRALX_FEX_KEYRING`, `CATEDRALX_FEX_ACTIVE_KEY_ID`; la evidencia lleva `evidence_key_id`, incluido en la firma.
- **AEX/aprobación humana:** `CATEDRALX_APPROVAL_KEYRING`, `CATEDRALX_APPROVAL_ACTIVE_KEY_ID`; los tokens incluyen `key_id`.

Cada keyring valida que sea un objeto JSON, que la clave activa exista y que todos los identificadores/secretos sean válidos, con un mínimo de 32 bytes por secreto. Las claves no presentes en el keyring se rechazan. Los nombres de variables legacy siguen funcionando como compatibilidad temporal; no son una rotación coordinada y deben retirarse después de migrar configuración y consumidores.

### Validación ejecutada en el clon

- `tests/test_order_safety.py`: **34 passed**.
- Suite completa: **175 passed**.
- `compileall` para los tres módulos de firma: aprobado.
- `git diff --check`: limpio.

### Procedimiento de rotación recomendado

1. Crear la nueva clave aleatoria en el gestor de secretos; no pegarla en repositorios, logs ni chats.
2. Desplegar primero el keyring con clave antigua y nueva, manteniendo antigua como activa.
3. Verificar que todos los consumidores reconocen ambas claves y que los artefactos existentes siguen validándose.
4. Cambiar solo el identificador activo a la clave nueva; verificar que los nuevos artefactos usan el nuevo `key_id` y los artefactos dentro de TTL siguen validándose con la antigua.
5. Esperar más que el TTL máximo de cada artefacto, más margen de reloj; verificar que no hay procesos consumidores atrasados.
6. Retirar la clave antigua, comprobar que un artefacto firmado con ella se rechaza y que la clave nueva sigue operativa.
7. Guardar evidencia de pruebas y registrar quién autorizó el cambio, sin registrar valores secretos.

### Estado y límites

**H3: implementación de keyrings y compatibilidad verificada en el clon; rotación operativa aún no ejecutada.** No se generaron ni cambiaron secretos reales, no se modificó el entorno de producción y no se retiró ninguna clave. Las pruebas dedicadas en `tests/test_order_safety.py` verifican solapamiento, cambio de clave activa y rechazo tras retirar claves antiguas para DSX, FEX y aprobación AEX. La suite completa también fue ejecutada tras estos cambios. No hubo commit, push, merge, deploy ni operación financiera real.


### Nota de verificación posterior de H3 — discrepancia del script integral

En la repetición posterior a los cambios, la suite directa con `PYTHONPATH=elite:.` pasó: **175 passed**; `git diff --check` y `compileall` también terminaron sin errores. Sin embargo, al ejecutar `scripts/verify_isolated_safety.sh`, la fase de recolección de pytest falló antes de ejecutar pruebas: `tests/test_cognitive_state.py` y `tests/test_panic_integration.py` importan `build_cognitive_report`, que no existe en `elite/REASON/cognitive_state.py` en el estado actual. El script pone la raíz antes de `elite` en `PYTHONPATH`, a diferencia del comando directo que sí pasó. Esta discrepancia de imports no fue corregida dentro de H3 y debe resolverse antes de considerar verde la verificación integral. Por transparencia, no se considera aprobado el script completo en esta última ejecución.


## Verificación final de frontera SCX → DSX → FEX/MSX — 2026-10-24

Esta nota es posterior y prevalece sobre las observaciones históricas de discrepancia del script integral que aparecen arriba.

### Cambios consolidados en el clon aislado

- `elite/REASON/cognitive_state.py` contiene las funciones puras de cálculo cognitivo SCX y ya no importa FEX ni MSX.
- `elite/REASON/report_composition.py` reúne explícitamente los resultados cognitivos con la memoria de FEX y la trazabilidad de MSX. No impone bloqueos ni autoriza ejecución financiera.
- El orquestador consume la composición y aplica el resultado del gate DSX; los campos `hard_block` que quedan están en el límite de enforcement del orquestador, no en la salida de cálculo SCX.
- AEX exige una autorización DSX firmada, de vida corta, vinculada al hash de la decisión y el precio exactos. Un diccionario sin firma, un token de aprobación sin gate DSX, una autorización expirada o una decisión/precio distintos se rechazan.
- Se mantiene `financial_execution_authorized: false`. El flujo sigue siendo de orden local pendiente; no conecta ni envía órdenes a un broker.

### Validación repetida después de la refactorización

- Suite completa: **175 passed**.
- `scripts/verify_isolated_safety.sh`: **exit 0**; suite completa, `git diff --check`, análisis sintético sin trading/órdenes y bloqueo de emergencia aprobados.
- `compileall -q elite tests`: aprobado.
- `git diff --check`: aprobado.
- Búsqueda de imports cruzados en `cognitive_state.py`: ninguno.
- Pruebas dedicadas existentes cubren identidad de aprobación falsificada, gate DSX falsificado, decisión/precio distintos, expiración, token de aprobación sin gate y rotación de claves.

### Límites y disposición

La fase técnica queda **validada en el clon para revisión independiente**, no aprobada para producción. El proveedor real de identidad de aprobadores sigue sin configurarse; la rotación de claves de producción no se ha ejecutado; la suite no prueba resiliencia de disco ni concurrencia multiproceso completa; y el backtest disponible no demuestra una ventaja estable neta de costos. La autorización DSX solo habilita la creación local de una orden pendiente en pruebas; no autoriza transacciones financieras reales.

No se modificó el repositorio principal `CatedralX`; sus cambios preexistentes se conservaron. No hubo commit, push, merge, despliegue, cambio de secretos de producción ni operación financiera.


## Matriz de aceptación canónica — revisión independiente previa a liberación

Fecha de revisión: 2026-10-24. Alcance: inspección de contratos y ejecución de pruebas en `CatedralX-verify`; sin escritura en el repositorio principal.

### Criterio de estados

- **Verificado:** hay evidencia de código y prueba concreta para el alcance indicado.
- **Parcial:** existe implementación o prueba, pero no cubre toda la responsabilidad canónica o falta validación operacional.
- **Pendiente:** no hay evidencia suficiente de implementación/validación.
- **Bloqueado:** no puede aprobarse la liberación por una brecha crítica, dependencia no configurada o evidencia contradictoria.

### Matriz

| Requisito / frontera | Evidencia inspeccionada | Estado | Brecha / criterio para aceptar |
|---|---|---|---|
| SCX calcula coherencia y contraevidencia; DSX consume y bloquea sin recalcular | `elite/REASON/cognitive_state.py`; `elite/DSX/DEFENSE/guards.py`; `tests/test_vector_contracts.py` | Verificado en lógica aislada | Confirmar la misma ruta con entradas reales controladas y firma independiente; no equivale a validación predictiva. |
| SCX → DSX: disonancia, contraevidencia no válida y pánico bloquean | `cognitive_execution_guard`; `tests/test_vector_contracts.py`; `tests/test_panic_integration.py` | Verificado en pruebas sintéticas | Falta auditoría independiente de todos los entrypoints y consumidores operativos. |
| FEX → SCX: memoria/resultados históricos y calibración | `elite/FEX/FEEDBACK/feedback_loop.py`; `CATEDRAL_COGNITIVE_STATE_V4_2.md` | Parcial | El resumen de memoria existe, pero la calibración probabilística Platt/isotónica, Brier/ECE y la conexión histórica canónica no están demostradas. No etiquetar confianza heurística como probabilidad. |
| FEX → DSX: evidencia de gobernanza completa, íntegra y autenticada | `elite/FEX/GOVERNANCE/sustainability.py`; `tests/test_vector_contracts.py`; `tests/test_acceptance_contract.py` | Verificado en pruebas sintéticas | La clave y el reporte de prueba no prueban la configuración de producción; falta integrar y revisar gestión de secretos real. |
| MSX: procedencia por ciclo y rechazo de IDs duplicados | `elite/MSX/provenance.py`; `tests/test_vector_contracts.py`; `tests/test_acceptance_contract.py` | Parcial | Está probado el agregador y el rastro del informe cognitivo; falta demostrar instrumentación consistente de todos los vectores, versiones y dependencias en cada ciclo. |
| MSX → vectores: salud/telemetría observacional separada de enforcement DSX | `elite/PERCEIVE/bunker.py`; `elite/DSX/DEFENSE/defense.py`; `elite/DSX/DEFENSE/guards.py` | Parcial | Falta contrato transversal completo que pruebe detección de degradación, propagación a DSX y ausencia de decisiones de bloqueo dentro de MSX. |
| DSX → AEX: firma válida vinculada a intención/precio, TTL y aprobación separada | `elite/DSX/DEFENSE/guards.py`; `elite/AEX/DECISION/ordenes.py`; `tests/test_order_safety.py` | Verificado en pruebas aisladas | La autenticación real del aprobador sigue bloqueada hasta integrar un verificador OIDC/IdP confiable. La orden local pendiente no es ejecución financiera. |
| H1: ciclo real del orquestador integra FEX → DSX → AEX stub y falla cerrado si falta evidencia | `elite/REASON/orchestrator.py`; `tests/test_acceptance_contract.py` | Verificado en clon con datos sintéticos | No habilitar uso productivo mientras no exista proveedor FEX real y revisión independiente. |
| H2: identidad externa y permiso del aprobador | `elite/AEX/DECISION/ordenes.py`; pruebas de identidad en `tests/test_order_safety.py` | Bloqueado para producción; mitigado en clon | Falta proveedor real que valide firma, issuer, audience, expiración, nonce/replay y permisos. El proveedor sintético solo prueba el contrato. |
| H3: rotación coordinada de claves AEX/DSX/FEX | `elite/AEX/DECISION/ordenes.py`; `elite/DSX/DEFENSE/guards.py`; `elite/FEX/GOVERNANCE/sustainability.py`; `tests/test_order_safety.py` | Verificado en clon; operación pendiente | Keyrings versionados y pruebas de solapamiento/retiro reportadas. No se ejecutó rotación real, no se cambió Azure Key Vault y no se retiraron secretos heredados de producción. |
| H4: persistencia, recuperación e idempotencia bajo concurrencia | `tests/test_acceptance_contract.py`; `tests/test_order_safety.py` | Pendiente | Hay pruebas de ledger y token de un solo uso en escenarios aislados; no hay evidencia suficiente de atomicidad multiproceso, recuperación ante caída a mitad de escritura, bloqueo de archivo/DB, duplicados concurrentes y reconciliación. |
| Panic y evidencia incompleta: rechazo sin escribir estado/feedback indebido | `tests/test_panic_integration.py`; `tests/test_acceptance_contract.py`; `scripts/verify_isolated_safety.sh` | Verificado en pruebas sintéticas | Extender prueba de fallo a persistencia y concurrencia cuando se trabaje H4. |
| MCX calcula tamaño; DSX/AEX conservan límites finales | `elite/MCX/OPTIMIZE/`; `elite/AEX/DECISION/limites.py`; `elite/AEX/DECISION/operador.py` | Parcial | Hay rutas superpuestas de Kelly/optimización; falta reconciliar el contrato único y probar que ninguna ruta omite límites finales. |
| Estado canónico y compatibilidad de consumidores | `elite/REASON/schemas.py`; `elite/REASON/report_composition.py`; pruebas de ciclo | Parcial | El campo opcional `cognicion` mantiene compatibilidad básica; falta inventario completo de consumidores y pruebas de contrato/serialización de versiones. |
| No trading/no broker/no despliegue | `elite/AEX/ejecutor.py`; `tests/test_acceptance_contract.py`; `scripts/verify_isolated_safety.sh` | Verificado en pruebas aisladas | Mantener AEX como stub y no conectar credenciales de broker en esta fase. |
| Comparación con el repositorio principal antes de integrar | Estado local del clon registrado; repositorio principal contiene cambios preexistentes del usuario | Pendiente | Preparar diff por archivo y clasificar cada cambio como trasladar, adaptar, conservar solo en clon o descartar. No aplicar cambios al original durante esta revisión. |
| Firma independiente y dictamen de liberación | Este expediente y suite interna | Bloqueado | La prueba del autor no sustituye la revisión independiente. No hay aprobación para producción ni integración al repositorio principal. |

### Validación ejecutada en esta pasada

Comando ejecutado en `CatedralX-verify`:

- `PYTHONPATH=elite:. python -m pytest -q`: **175 passed**.
- `scripts/verify_isolated_safety.sh`: **ALL ISOLATED SAFETY CHECKS PASSED**; incluye suite, `git diff --check`, análisis sintético sin trading/órdenes y bloqueo de emergencia.
- `python -m compileall -q elite tests`: completado sin errores.
- `git diff --check`: correcto.

El estado Git mostrado corresponde al clon aislado y enumera cambios locales/untracked del trabajo de consolidación; no es un diff entre repositorios. No se usó `git reset`, `clean`, commit, push, merge ni deploy.

### Dictamen provisional

**Aceptación técnica parcial del clon para revisión independiente; liberación bloqueada.** Los tests respaldan contratos sintéticos concretos, no certifican autenticación productiva, calibración estadística, resiliencia multiproceso ni ventaja predictiva. Los bloqueos principales son H2 (IdP real), H3 (rotación operacional), H4 (persistencia/concurrencia) y la comparación archivo por archivo contra el repositorio principal. El siguiente cambio debe responder a una brecha de esta matriz; no se autorizan módulos duplicados ni traslado automático de cambios.


### H4 — primera prueba de concurrencia y límite residual

Después de registrar la matriz se añadió `test_concurrent_retries_with_same_approval_never_persist_duplicate_orders` a `tests/test_order_safety.py`. Ocho intentos concurrentes comparten una autorización sintética; la prueba comprueba que no aparezcan órdenes persistidas duplicadas ni más de una entrada de historial para el mismo hash de aprobación.

Validación posterior a esta prueba:

- `tests/test_order_safety.py`: **35 passed**.
- Suite completa: **176 passed**.
- `scripts/verify_isolated_safety.sh`: **ALL ISOLATED SAFETY CHECKS PASSED**.
- `compileall -q elite tests`: correcto.
- `git diff --check`: correcto.

**Resultado limitado:** se verificó la no duplicación en este escenario concurrente dentro del mismo proceso; H4 no queda cerrado. Persiste una ventana de recuperación: si el proceso cae después de crear el marcador `.used` y antes de publicar atómicamente `orden.json`, la autorización puede quedar consumida sin orden canónica. La comprobación de concurrencia no simula caída abrupta ni varios procesos/hosts y no demuestra transacción atómica entre orden, marcador e historial. El siguiente cambio de H4 debe diseñar y probar una recuperación idempotente de esa ventana antes de declarar resiliencia.


## Décima pasada — H3: rotación coordinada de claves (clon aislado)

Fecha: 2026-10-24. Alcance: autenticación de artefactos DSX, evidencia FEX y aprobaciones AEX. Sin cambios de secretos reales ni configuración de producción.

### Contrato implementado

- Cada familia admite un keyring versionado y una clave activa:
  - DSX: `CATEDRALX_DSX_AUTH_KEYRING` + `CATEDRALX_DSX_AUTH_ACTIVE_KEY_ID`.
  - FEX: `CATEDRALX_FEX_KEYRING` + `CATEDRALX_FEX_ACTIVE_KEY_ID`.
  - AEX approvals: `CATEDRALX_APPROVAL_KEYRING` + `CATEDRALX_APPROVAL_ACTIVE_KEY_ID`.
- Los keyrings se reciben como JSON que mapea identificadores de clave a secretos; cada secreto debe tener al menos 32 bytes UTF-8.
- El artefacto firmado incluye el identificador de clave. La firma/verificación selecciona esa clave, no simplemente la activa actual.
- Durante la ventana de solapamiento, la nueva clave firma y la anterior sigue verificando artefactos previamente emitidos. Retirar una clave hace que los artefactos que dependen de ella fallen cerrados.
- Se mantiene compatibilidad temporal con los secretos heredados (`CATEDRALX_DSX_AUTH_SECRET`, `CATEDRALX_FEX_EVIDENCE_SECRET`, `CATEDRALX_APPROVAL_SECRET`) para no romper automáticamente los entornos existentes; esa compatibilidad no sustituye la migración planificada al keyring.

### Pruebas

- DSX: firma con la clave activa nueva, verificación durante solapamiento y rechazo tras retirar la clave antigua del artefacto.
- FEX: firma de evidencia con ID de clave, verificación durante solapamiento y rechazo después de retirar esa clave.
- AEX: token de aprobación firmado con la nueva clave sigue verificándose mientras la clave identificada continúa en el keyring.
- Pruebas dirigidas: **49 passed**.
- Suite completa: **179 passed**.
- `git diff --check` y `compileall`: ejecutados sin error en la cadena de validación.

### Procedimiento de rotación recomendado

1. Generar claves nuevas fuera del repositorio, en un gestor de secretos; nunca guardar secretos reales en el código, tests, tickets o este documento.
2. Desplegar el keyring con clave antigua y nueva, conservando como activa la antigua.
3. Confirmar que todos los validadores reconocen ambas claves.
4. Cambiar el ID activo a la nueva y verificar firma/validación en pruebas.
5. Esperar más que la vida máxima de los artefactos emitidos con la clave anterior (DSX 30 s; aprobaciones 120 s; FEX requiere definir una política de antigüedad/retención de evidencias).
6. Retirar la antigua solo tras verificar que no existen artefactos vigentes que dependan de ella. Mantener un procedimiento de recuperación controlado.

### Límites y estado

H3 está implementado y probado en el clon aislado para los tres flujos. No se generaron ni rotaron secretos reales, no se modificó ningún entorno de despliegue y no se hizo commit/push/merge/deploy. La compatibilidad heredada sigue habilitada; la migración operativa y la política de retención de evidencias FEX deben completarse antes de declarar rotación productiva cerrada. AEX continúa siendo un flujo de autorización de órdenes pendientes; no se habilita ejecución financiera real.


## Décima pasada — H3: rotación coordinada de claves con keyrings versionados

Fecha: 2026-10-24. Cambios y pruebas en el clon aislado `CatedralX-verify`.

### Cambio aplicado

- DSX incorpora `CATEDRALX_DSX_AUTH_KEYRING` y `CATEDRALX_DSX_AUTH_ACTIVE_KEY_ID`.
- FEX incorpora `CATEDRALX_FEX_KEYRING` y `CATEDRALX_FEX_ACTIVE_KEY_ID`.
- AEX/aprobaciones incorpora `CATEDRALX_APPROVAL_KEYRING` y `CATEDRALX_APPROVAL_ACTIVE_KEY_ID`.
- Cada keyring identifica una clave activa para firmar y conserva claves anteriores configuradas para verificar artefactos aún vigentes durante la ventana de solapamiento.
- Los artefactos firmados incluyen el identificador de clave (`key_id` / `evidence_key_id`); la verificación selecciona esa clave exacta y rechaza identificadores desconocidos o retirados.
- El modo heredado mediante variables secretas individuales se conserva como compatibilidad temporal; no se han cambiado secretos del entorno ni se ha activado un keyring en producción.

### Pruebas y validación

- Añadí pruebas de rotación/solapamiento para tokens de aprobación y autorizaciones DSX, así como rechazo de identificadores desconocidos.
- `tests/test_order_safety.py`: **40 passed**.
- Suite completa: **181 passed**.
- `git diff --check`: limpio.
- `compileall`: aprobado para los módulos modificados.
- `git status --short` revisado en `CatedralX-verify`; hay cambios preexistentes en el clon que se conservaron, no se limpiaron ni revirtieron.

### Procedimiento de rotación requerido antes de producción

1. Generar la nueva clave con un gestor de secretos; no usar claves de ejemplo ni pegarlas en repositorios.
2. Distribuir la nueva clave a todos los verificadores manteniendo temporalmente la clave anterior.
3. Promover el identificador nuevo como activo en los emisores de ese dominio (DSX, FEX o aprobación) y comprobar emisión/verificación.
4. Mantener el solapamiento al menos durante la vida máxima del artefacto firmado y cualquier ventana de recuperación aprobada.
5. Retirar la clave antigua únicamente tras confirmar que no quedan artefactos legítimos pendientes; registrar responsable, fecha y versión.
6. Si hay sospecha de compromiso, no usar la rotación gradual como sustituto de revocación: bloquear el flujo, retirar la clave comprometida de los verificadores y exigir nueva autorización de los artefactos pendientes.

### Límites

**H3 implementado y validado en el clon; despliegue operativo de rotación pendiente.** La compatibilidad heredada permite migrar sin cambiar producción ahora mismo, pero no es el estado final deseado. Las claves reales deben residir en un gestor de secretos, con permisos mínimos, auditoría y distribución coordinada. No se han creado ni cambiado secretos reales. No hubo commit, push, merge, deploy ni operación financiera. El repositorio original no se modificó en esta intervención.

## Décima pasada — H3: rotación versionada de claves (clon aislado)

Fecha: 2026-10-24. Cambios/validación exclusivamente en `CatedralX-verify`.

### Contrato de rotación

Se verifica el soporte de keyrings versionados para los tres límites HMAC:
- DSX: `CATEDRALX_DSX_AUTH_KEYRING` + `CATEDRALX_DSX_AUTH_ACTIVE_KEY_ID`.
- FEX: `CATEDRALX_FEX_KEYRING` + `CATEDRALX_FEX_ACTIVE_KEY_ID`.
- AEX aprobación: `CATEDRALX_APPROVAL_KEYRING` + `CATEDRALX_APPROVAL_ACTIVE_KEY_ID`.

El ID de clave se incluye en cada artefacto firmado. La clave activa firma nuevos artefactos; las claves de solapamiento configuradas verifican los artefactos emitidos antes de completar la rotación. Una clave desconocida, ausente, corta o sin ID activo válido produce rechazo. Los nombres de entorno de secreto legacy se mantienen como modo de compatibilidad y deben retirarse tras una migración operativa planificada.

### Validación observada

- `tests/test_order_safety.py`: **40 passed**.
- Suite completa: **197 passed**.
- `git diff --check`: limpio.
- `compileall`: aprobado para DSX, FEX, AEX y pruebas de seguridad.

### Procedimiento operativo seguro

1. Generar una clave nueva en un gestor de secretos; no pegar secretos reales en chat, logs o repositorio.
2. Publicar el keyring con clave antigua y nueva, con ID activo aún en la antigua.
3. Cambiar el ID activo a la nueva clave; confirmar que nuevos artefactos llevan el nuevo ID y que los artefactos antiguos válidos aún verifican durante el solapamiento.
4. Esperar a que expire la vida máxima de artefactos y cerrar procesos que puedan conservar artefactos antiguos.
5. Retirar la clave antigua y verificar que un artefacto firmado con ella ya no se acepta.
6. Repetir coordinadamente para DSX, FEX y AEX, sin mezclar IDs ni reutilizar secretos entre dominios.

### Estado y límites

**H3: soporte de rotación versionada y solapamiento validado en pruebas; rotación real de secretos no ejecutada.** No se modificaron secretos de producción, variables del host, Azure Key Vault, despliegues ni credenciales. No se hicieron commit/push/merge/deploy ni operaciones financieras. Antes de producción falta documentar y ensayar el procedimiento de despliegue del keyring en el gestor de secretos real, el responsable/ventana de rotación y el plan de recuperación. El modo legacy sigue habilitado por compatibilidad y debe considerarse deuda de migración.


## Undécima pasada — revalidación final H3 y actualización del Mapa Maestro

Fecha: 2026-10-24. Esta entrada supersede los conteos de pruebas anteriores registrados en las pasadas H3.

### Resultado de la revalidación
- Pruebas enfocadas `tests/test_sustainability_governance.py` + `tests/test_order_safety.py`: **61 passed**.
- Suite completa: **224 passed**.
- `scripts/verify_isolated_safety.sh`: aprobado; repitió suite completa, `git diff --check`, smoke de análisis sintético sin órdenes y bloqueo de emergencia.
- `compileall` para DSX/FEX y pruebas H3: aprobado.
- Se verificó el estado del worktree; cambios previos y archivos no rastreados permanecen preservados. No se hizo limpieza ni reversión.

### Inventario empresarial actualizado mediante lecturas externas autorizadas
- Se amplió `INVENTARIO_TECNICO_COMPLEMENTARIO_v0.1_2026-10-24.md` con asociaciones actuales de alias/deployment de Vercel, proyectos Supabase, referencias locales, funciones activas, RLS y avisos de seguridad.
- Se amplió `MAPA_MAESTRO_DECOX_v0.2_2026-10-24.md` con los riesgos prioritarios y se corrigió la recomendación anterior para no reasignar el alias de Interactive antes de decidir cuál versión debe ser pública.
- En Tricentric, los advisories de `SECURITY DEFINER` se contrastaron con definiciones y ACL: las firmas revisadas no permiten EXECUTE a `anon`, comprueban `auth.uid()` y configuran `search_path` vacío; aun requieren pruebas entre cuentas y revisar auxiliares.
- En MAGIS comercial, las tablas sin políticas identificadas tienen RLS activo y no conceden SELECT a `anon` ni `authenticated`; revisar autorización server-side antes de decidir políticas.
- Se detectó que los enlaces locales de Interactive y SystemDecode apuntan al mismo proyecto Supabase. Falta confirmar si es arquitectura deliberada o un riesgo de aislamiento transaccional.

### Límites
Las consultas SQL fueron SELECT a catálogos y privilegios de sistema; no se leyeron filas de negocio. No se leyeron archivos `.env`, no se solicitaron valores descifrados, no se cambiaron variables, secretos, permisos, funciones, políticas, DNS, aliases o deployments. No se ejecutaron pagos reales ni operaciones financieras. H3 sigue siendo soporte de rotación probado en aislado; la rotación real y su configuración en gestor de secretos permanecen pendientes. Sin commit, push, merge o deploy.
