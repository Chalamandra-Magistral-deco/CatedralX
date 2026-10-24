# CHALAMANDRA CORE — Especificación maestra

**Estado:** base de implementación preparada; no habilita producción ni trading real.  
**Repositorio de trabajo:** `CatedralX-verify` (copia aislada).  
**Regla:** consolidar las capacidades existentes; no crear módulos paralelos solo para renombrarlos.

## 1. Propósito

Chalamandra Core es el núcleo de coordinación cognitiva, financiera y adaptativa de Chalamandra Magistral DecoX. Convierte observaciones verificadas en análisis, decisiones sujetas a restricciones, acciones autorizadas y resultados medibles. La Catedral aporta la base modular; el estado neurocomputacional regula el ciclo; los motores especializados permanecen desacoplados.

No se presume equivalencia biológica literal. `attention`, `confidence`, `uncertainty`, `energy`, `stress`, `curiosity`, `prediction_error` y `learning_rate` son variables computacionales, no neurotransmisores ni diagnósticos fisiológicos.

## 2. Principios no negociables

1. **Un solo coordinador:** reutilizar el orquestador existente; no introducir un segundo ciclo maestro en paralelo.
2. **Seguridad independiente:** DSX puede vetar cualquier propuesta. MCX, el predictor y el aprendizaje no pueden anular ese veto.
3. **Evidencia antes que afirmaciones:** cada decisión registra ciclo, fuente, tiempo, versión, entradas y motivo; no inventar precisión, PnL ni resultados.
4. **Fallos cerrados:** datos ausentes, vencidos, corruptos, no finitos o firmas inválidas implican rechazo/HOLD.
5. **Separación análisis/ejecución:** el análisis no coloca órdenes. Toda acción financiera requiere los controles y autorizaciones explícitos existentes.
6. **Aprendizaje controlado:** entrenar en datos separados; comparar contra la versión vigente; promover solo con criterios predefinidos y posibilidad de reversión.
7. **Contabilidad independiente:** resultados económicos netos de comisiones, deslizamiento, financiación y demás costes aplicables.
8. **Cambios reversibles:** trabajar en la copia aislada, conservar cambios locales, no desplegar ni modificar DNS/producción como parte de esta fase.

## 3. Arquitectura lógica y correspondencia con el código

Los nombres RSX, FEX, AEX, MCX, DSX y FLX son etiquetas de arquitectura. No deben convertirse en paquetes nuevos si ya hay una responsabilidad equivalente.

| Vector conceptual | Responsabilidad | Integración preferida |
|---|---|---|
| RSX — Percepción | Ingesta, validación, frescura y normalización | `PERCEIVE` y adaptadores de fuentes existentes |
| FEX — Memoria/evidencia | Contexto, historial, predicciones y resultados | `FEX` y su ledger de feedback/gobernanza |
| AEX — Análisis/acción | Señales, predicción, selección de acción e intención | `REASON` para análisis; `AEX` para intención/órdenes protegidas |
| MCX — Regulación | Atención, incertidumbre, carga, energía y límites adaptativos | Reutilizar estado cognitivo y controles existentes; no duplicarlos |
| DSX — Protección | Veto, emergencia, autorización, permisos y límites | `DSX.DEFENSE`; autoridad independiente y fail-closed |
| FLX — Aprendizaje | Error de predicción, evaluación y promoción controlada | `FEX.FEEDBACK` y entrenadores existentes tras comparar duplicados |
| MSX — Trazabilidad | Procedencia por ciclo, versiones, hashes y auditoría | `MSX.provenance` |
| Resultados | Costes, PnL, exposición, drawdown, calidad y errores | Ledger contable independiente y motor de simulación/backtest |

## 4. Contrato mínimo de estado

El estado canónico por ciclo debe contener como mínimo:

- `schema_version`: versión explícita del contrato.
- `cycle_id`: identificador único y estable del ciclo.
- `observed_at`: timestamp con zona horaria.
- `source_status`: fuentes utilizadas, frescura y validación.
- `context_ref`: referencia a memoria/evidencia, no secretos.
- `signals`: señales con nombre, dirección, confianza y tipo de confianza.
- `uncertainty`: incertidumbre explícita; no confundir heurísticas con probabilidades calibradas.
- `prediction`: hipótesis, horizonte, precio/resultado de referencia y versión del modelo.
- `prediction_error`: nulo hasta que venza el horizonte y exista resultado válido; luego resultado observado menos predicción, con definición de signo documentada.
- `regulation`: atención, energía, estrés computacional, curiosidad y tasa de aprendizaje, todos acotados y versionados.
- `decision`: propuesta, razón, restricciones y estado `HOLD` cuando haya evidencia insuficiente.
- `risk_gate`: resultado DSX, motivos, firma, expiración y vinculación exacta a intención/valores.
- `action`: `NONE`, `SIMULATE`, `PENDING_APPROVAL` o estado equivalente; nunca inferir ejecución por una propuesta.
- `outcome`: costes y resultado real solo después de observarlos.
- `provenance`: versiones de módulos, hashes de entradas y referencias de trazabilidad.

No introducir una segunda clase de estado hasta demostrar que los contratos existentes no pueden ampliarse de forma compatible.

## 5. Ciclo maestro

1. Percibir y validar esquema, origen, timestamps y frescura.
2. Recuperar memoria y evidencia relevante.
3. Calcular señales y desacuerdo entre fuentes.
4. Producir predicción con horizonte y nivel de incertidumbre explícitos.
5. Registrar predicción antes del resultado; no calcular error anticipadamente.
6. Actualizar variables regulatorias dentro de límites establecidos.
7. Proponer decisión y justificarla con evidencia.
8. Ejecutar DSX de forma independiente; veto o evidencia inválida => `HOLD`.
9. En modo investigación, simular; en modo paper, registrar ejecución simulada; cualquier modo financiero real exige habilitación separada y autorización humana verificable.
10. Registrar resultado y costes cuando existan.
11. Evaluar rendimiento y deriva; entrenar/promover versiones únicamente mediante validación fuera de muestra.
12. Emitir trazabilidad del ciclo y métricas.

## 6. Modos operativos

- `RESEARCH`: análisis de datos, sin crear órdenes.
- `BACKTEST`: simulación histórica reproducible con separación temporal y costes configurados.
- `PAPER`: mercado/snapshot permitido, órdenes solo simuladas.
- `LIVE`: deshabilitado por defecto. No se activa mediante este documento ni por pasar pruebas unitarias. Requiere autorización explícita, controles de riesgo, identidad verificable, límites de capital, reconciliación contable, kill switch probado y validación operativa independiente.

Los modos deben ser explícitos y fail-closed. La ausencia de configuración significa `RESEARCH`, nunca `LIVE`.

## 7. Contrato de error de predicción y aprendizaje

`prediction_error` solo se calcula cuando el horizonte ha vencido y el resultado procede de una fuente válida. Debe guardar predicción original, resultado observado, timestamp, fuente, horizonte, versión del modelo y fórmula aplicada. Los registros no se sobrescriben; las correcciones se agregan como eventos auditables.

El aprendizaje no modifica DSX, secretos, límites de riesgo, permisos, modo operativo ni el código en ejecución. La promoción de modelos requiere evaluación fuera de muestra, comparación contra baseline, límites de degradación, registro de artefacto y rollback.

## 8. Puertas de aceptación

- Contratos tipados y versionados; validación de valores no finitos y timestamps sin zona horaria.
- Datos faltantes o caducados producen `HOLD` y no escriben órdenes.
- Cada ciclo mantiene trazabilidad única; se rechazan IDs duplicados y evidencia manipulada.
- DSX rechaza evidencia ausente, alterada, expirada, no vinculada a la intención o con emergencia activa.
- Ninguna prueba de análisis puede invocar el escritor de órdenes ni un adaptador de exchange.
- Feedback no inventa resultados y no entrena automáticamente con etiquetas pendientes.
- Backtest reproduce resultados con configuración/versiones fijadas e incluye costes.
- Ledger reconcilia saldo, posiciones, exposición y PnL sin mezclar datos empresariales con credenciales.
- Pruebas de regresión completas y diff revisado antes de cada promoción.

## 9. Orden de implementación

**Fase 0 — Congelar límites:** esta especificación en la copia aislada; no tocar la copia original ni producción.

**Fase 1 — Contrato:** adaptar los esquemas existentes para cubrir los campos mínimos, sin crear una clase paralela innecesaria.

**Fase 2 — Ciclo sintético extremo a extremo:** percepción → memoria → análisis/predicción → regulación → DSX → intención AEX en modo no ejecutable → feedback simulado → procedencia. Probar fallos y emergencias.

**Fase 3 — Evaluación financiera:** backtest reproducible, baseline, comisiones, deslizamiento, drawdown, exposición y ledger.

**Fase 4 — Aprendizaje controlado:** evaluación fuera de muestra, promoción versionada y rollback.

**Fase 5 — Integración empresarial:** interfaces/adaptadores independientes para automatización, analítica y productos DecoX; cada dominio con permisos, datos y métricas separados.

**Fase 6 — Revisión de preparación operativa:** lista de verificación independiente; LIVE continúa deshabilitado hasta aprobación explícita.

## 10. Fuera de alcance de esta preparación

No se habilita trading real, no se conectan credenciales nuevas, no se alteran límites de seguridad, no se despliega, no se cambia DNS, no se borran ni se fusionan copias y no se declara rentabilidad sin evidencia.

## Definición de terminado para el núcleo inicial

El núcleo inicial está listo cuando un ciclo sintético reproducible recorre las interfaces existentes, genera un estado y una traza verificables, mide error únicamente con resultados disponibles, recibe el veto DSX cuando corresponde, produce solo intención no ejecutable, y supera pruebas automatizadas sin escribir en rutas de estado reales ni realizar llamadas a exchanges.
