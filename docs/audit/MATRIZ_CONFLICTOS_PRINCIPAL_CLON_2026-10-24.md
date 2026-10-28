# MATRIZ DE CONFLICTOS — PRINCIPAL vs CLON
Fecha: 2026-10-24
Alcance: revisión comparativa de cuatro contratos críticos. Solo lectura del repo principal; este informe se guarda únicamente en CatedralX-verify.

## Dictamen ejecutivo
**No integrar ni copiar archivos completos.** Hay cambios del principal que el clon no incorpora y cambios de gobernanza del clon que no deben sustituir las restricciones dinámicas del principal. El principal permanece intacto.

| Archivo | Principal actual vs HEAD | Clon actual vs HEAD | Decisión recomendada | Riesgo / acción posterior |
|---|---|---|---|---|
| `elite/REASON/orchestrator.py` | +47 líneas: integra `DynamicConstraintInputs` / `evaluate_dynamic_constraints`, propaga `dynamic_constraints` en `SensoryInput` y fuerza HOLD ante violaciones medidas. | +144/-7 líneas: integra reporte SCX, puerta DSX, evidencia FEX opcional, ID de ciclo y handoff AEX de revisión. No incorpora restricciones dinámicas del principal. | **Combinar selectivamente; no resolver todavía.** Conservar ambos contratos: restricciones dinámicas y reporte cognitivo/DSX. | Riesgo alto de regresión funcional si se usa el orquestador del clon sin el control dinámico del principal. Riesgo adicional de desacople: el clon valida firma DSX pero su ruta AEX sigue siendo solo revisión y no pasa autorización a `preparar_intencion`; el diseño declara que no crea/ejecuta órdenes. Añadir pruebas de restricciones dinámicas + DSX/FEX ausente + pánico + ciclo trazable. |
| `elite/AEX/DECISION/ordenes.py` | Sin cambios locales frente a HEAD. | +281/-43 líneas: identidad externa, token HMAC con keyring, TTL, vínculo exacto de decisión/precio, consumo de un solo uso, gate DSX, escritura atómica e historial. | **Mantener la implementación del clon solo en el clon, pendiente de endurecimiento.** No copiar al principal aún. | Proveedor real de identidad no configurado; fallback legacy de clave sigue activo. El consumo del token se registra antes de persistir la orden: caída entre ambos pasos puede dejar autorización consumida sin orden; requiere reconciliación/recuperación y pruebas de concurrencia. El historial JSONL se escribe después de la orden y no es transacción atómica con ella. Validar además la política de rotación/revocación y permisos del directorio de aprobaciones. |
| `elite/REASON/schemas.py` | +1 campo en `SensoryInput`: `dynamic_constraints: Dict[str, Any]` con default. | +1 campo en `CathedralState`: `cognicion: Dict[str, Any]` con default. No incorpora `dynamic_constraints` en `SensoryInput`. | **Combinar ambos campos de forma compatible**, conservando los defaults y el orden de los campos existentes. | La ausencia de `dynamic_constraints` en el clon rompe la propagación de restricciones del principal. El campo `cognicion` permite el reporte nuevo. Probar constructores posicionales/por keyword y serialización del estado. |
| `elite/AEX/ejecutor.py` | +84/-13 líneas: validación de tamaño finito/no negativo, buy/sell con tamaño positivo, pánico por parámetro/archivo, autorización explícita, precio y confianza válidos; ejecución real sigue denegada. | Sin cambios locales frente a HEAD: solo permite etiquetas, bloquea por pánico/flags/hold y siempre niega ejecución real; no exige autorización, precio ni confianza. | **Preservar la versión endurecida del principal como requisito de seguridad; no copiarla a ciegas.** | El orquestador del clon llama `preparar_intencion(decision, size=0.0, ...)`. Al incorporar la versión estricta, buy/sell con tamaño cero levantaría error. Antes de combinar, cambiar el contrato de llamada para expresar explícitamente intención de revisión/HOLD, o definir una API review-only separada; no debilitar la validación para ocultar el desacople. |

## Evidencia de contratos y dependencias

### Orchestrator
- Principal: importa `DynamicConstraintInputs` y `evaluate_dynamic_constraints`; acepta `DYNAMIC_CONSTRAINTS`, rechaza claves desconocidas y marca HOLD ante infracciones medidas.
- Clon: usa `build_cognitive_report`, `cognitive_execution_guard`, `final_execution_guard`, verificación de autorización DSX y `preparar_intencion`.
- El clon clasifica explícitamente `signal_strength` como heurística, no probabilidad calibrada. Mantener esa distinción: SCX reporta, DSX aplica enforcement y FEX solo consume evidencia histórica/calibración.

### Ordenes
- El clon exige un token firmado y autorización DSX válida antes de persistir una orden **pendiente local**. Esto no autoriza ejecución financiera real.
- La comprobación de identidad depende de `APPROVER_IDENTITY_VERIFIER`; sin proveedor inyectado, la aprobación se deniega.
- Riesgo de recuperación: marcador de token consumido y archivo de orden no forman una única transacción durable. El idempotency check ayuda si la orden ya existe, pero no resuelve por sí solo una caída después de consumir el token y antes de escribir la orden.

### Executor
- El principal aplica validación de entrada más estricta que la versión del clon.
- Ambas versiones mantienen `trading_enabled=False`, `orders_created=False`, `orders_executed=False` y `execute_order` deniega la ejecución real.
- No activar broker ni órdenes reales.

## Pruebas que deben proteger cualquier combinación
1. `tests/test_dynamic_constraints.py` y `tests/test_economic_cycle.py` (existen solo en el principal): preservar y ejecutar al integrar restricciones dinámicas.
2. `tests/test_order_safety.py`: identidad ausente/no verificada, permisos, firma, TTL, decisión/precio/tamaño/razón alterados, token usado, pánico, DSX ausente o inválido, escritura y recuperación.
3. `tests/test_cathedral_vectors.py`: mantener contratos del executor y prohibición de ejecución real; actualizar pruebas si cambia la semántica review-only.
4. Pruebas nuevas de integración: restricciones dinámicas + reporte cognitivo + DSX fail-closed; constructor/serialización de `SensoryInput` y `CathedralState`; crash entre consumo de aprobación y persistencia; concurrencia de dos procesos con el mismo token.
5. Ejecutar la suite del clon con su script de verificación y PYTHONPATH documentado; una invocación genérica de `pytest -q` previamente falló en colección por `ModuleNotFoundError: PERCEIVE`, mientras que el script integral del clon pasó 210 pruebas.

## Orden seguro de resolución
1. No tocar el principal.
2. Resolver primero el contrato de `schemas.py`: preservar ambos campos con defaults compatibles.
3. Combinar `orchestrator.py` en una rama del clon, reintroduciendo la evaluación de restricciones dinámicas sin mezclarla con la responsabilidad cognitiva/DSX.
4. Alinear el handoff review-only del orquestador con el executor endurecido; no pasar señales heurísticas como probabilidad ni usar tamaño cero como una orden de compra/venta.
5. Endurecer recuperación/atomicidad de `ordenes.py` y probar concurrencia antes de considerar cualquier promoción.
6. Auditoría independiente y firma antes de cualquier release.

## Límites de esta revisión
Esto es una matriz de conflictos basada en diffs, contratos e inspección de puntos de llamada; no es una revisión semántica exhaustiva línea por línea ni aprobación de producción. No se modificó código. No se copiaron archivos. El repositorio principal no se modificó.

## Actualización de resolución aislada — 2026-10-24

Se aplicó una primera combinación **solo en CatedralX-verify**:
- `elite/REASON/schemas.py`: `SensoryInput.dynamic_constraints` añadido con `default_factory=dict`; se conserva `CathedralState.cognicion`.
- `elite/REASON/dynamic_constraints.py`: incorporado el evaluador de restricciones dinámicas que ya existía en el árbol principal.
- `elite/REASON/orchestrator.py`: acepta `DYNAMIC_CONSTRAINTS`, rechaza claves desconocidas con fail-closed, registra el informe en contexto/percepción y fuerza HOLD ante una infracción dura medida. Los datos ausentes bloquean crecimiento, pero no se etiquetan falsamente como infracción medida.
- `elite/AEX/ejecutor.py`: alineado en el clon con la versión de validación estricta del principal. El orquestador emite una intención AEX de revisión explícita como HOLD/tamaño cero; la señal analítica original se conserva en `requested_signal`. No se trata como orden.
- `tests/test_dynamic_constraints.py`: incorporado al clon.
- `tests/test_acceptance_contract.py`: añadidas pruebas de integración para infracción dinámica y clave desconocida; la prueba de handoff exige bloqueo de revisión porque no hay aprobación humana explícita.

### Verificación tras la combinación
- Script integral de seguridad aislada: **218 passed in 0.50s**.
- Prueba sintética: OK; trading deshabilitado, sin órdenes.
- Bloqueo de emergencia: OK; ciclo rechazado sin escribir estado ni feedback.
- `compileall`: OK.
- `git diff --check`: OK.
- Principal: mismo HEAD `428253d60534cea4492fa19cc1f00e1f2b70765f`; no se escribieron archivos del principal ni se hizo commit, push, merge o despliegue.

### Pendientes no resueltos
1. No se han ejecutado pruebas de concurrencia multiproceso ni de caída entre consumo de token y persistencia de orden.
2. El proveedor real de identidad y la rotación/revocación real de claves siguen sin configuración/validación independiente.
3. La suite y el smoke test no constituyen un backtest con costes completos ni demuestran edge neto estable.
4. No hay firma de auditor independiente ni autorización de producción.

**Estado:** combinación inicial en el clon, pruebas automatizadas verdes; no es aprobación de release y no habilita trading.

## Corrección adicional útil: recuperación tras caída antes de persistir orden

Se corrigió únicamente en el clon el hueco de recuperación entre el consumo del token y la escritura atómica de la orden:
- Se añadió un bloqueo exclusivo de generación con `fcntl.flock` para serializar intentos concurrentes entre procesos.
- Si el marcador de consumo existe pero no existe la orden canónica, un reintento solo puede recuperar dentro del TTL, con el mismo token firmado, el mismo aprobador registrado y bajo el bloqueo exclusivo.
- Si la orden ya existe, se mantiene la recuperación idempotente normal. Tokens vencidos, alterados o con marcador inconsistente siguen bloqueados.
- Se añadió `test_order_retry_recovers_after_crash_between_token_consumption_and_order_write`, que inyecta un fallo justo antes de escribir la orden y verifica recuperación en el reintento.

### Resultado tras la corrección
- Suite integral: **219 passed in 0.52s**.
- `compileall`: OK.
- `git diff --check`: OK.
- Prueba sintética: OK; trading deshabilitado, sin órdenes.
- Bloqueo de emergencia: OK.
- Repo principal: HEAD sin cambio (`428253d60534cea4492fa19cc1f00e1f2b70765f`) y 14 entradas de estado previas conservadas.

### Límite
La prueba cubre fallo inyectado y concurrencia en el entorno local Linux. Todavía falta una prueba de caída real del proceso/host y revisión independiente de la semántica de recuperación. Esto no autoriza trading ni producción.
