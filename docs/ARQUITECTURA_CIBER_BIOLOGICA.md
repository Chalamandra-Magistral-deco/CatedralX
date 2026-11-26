# Arquitectura Ciber-Biológica de CatedralX

> **Estado:** especificación arquitectónica objetivo basada en las láminas de referencia y contrastada con el árbol y los contratos documentados de CatedralX en esta rama. Distingue implementación en código, diseño conceptual y operación no verificada.
>
> **Regla de diseño:** la biomimética organiza responsabilidades y preguntas de ingeniería. No convierte una analogía biológica en una capacidad de software ni en evidencia de funcionamiento.

## 1. Visión: dos continentes y un puente criptográfico

La arquitectura se representa como dos dominios autónomos:

- **Continente interior — CatedralX:** motor experimental de razonamiento y análisis financiero. Valida observaciones, procesa contexto, calcula métricas, aplica guardas y produce resultados estructurados con evidencia.
- **Continente exterior — Agents:** sistema separado que admite y coordina tareas, invoca CatedralX, persiste candidatos, ejecuta verificación independiente y gestiona distribución condicionada.

El **Puente Criptográfico** es el conjunto de contratos, identificadores, evidencias y verificaciones que permite intercambiar resultados entre ambos dominios. No es un microservicio ni concede autoridad por sí mismo.

Frontera lógica objetivo:
1. Agents entrega una solicitud conforme al contrato de integración.
2. CatedralX valida las entradas y produce un `DecisionResult` estructurado.
3. Agents conserva el candidato y lo somete a verificación independiente.
4. Aceptación interna de CatedralX, aceptación independiente de Agents, autorización humana, despacho y ejecución son etapas distintas.
5. Ninguna salida de CatedralX se interpreta automáticamente como orden ejecutable.

Esta secuencia describe la frontera de responsabilidad; no demuestra que todas las rutas estén conectadas y operativas en runtime.

## 2. Mente bicameral: separación de responsabilidades

La imagen de dos hemisferios expresa una división funcional, no una afirmación neuroanatómica ni una equivalencia entre cerebro y software.

| Dominio visual | Sistema | Responsabilidad técnica | Límites |
|---|---|---|---|
| Hemisferio de precisión | CatedralX | Validar observaciones, razonar, calcular métricas, aplicar guardas y producir resultados estructurados | No es un servicio HTTP persistente por defecto; no se autoautoriza para ejecutar |
| Hemisferio de acción | Agents | Admitir y coordinar tareas, invocar el motor, persistir candidatos, verificar y distribuir bajo autorización | No sustituye el razonamiento financiero ni debe inventar métricas upstream |

La lámina menciona LLMs y redes neuronales del lado de Agents. Esa etiqueta debe tratarse como descripción del diseño visual hasta que el repositorio y la ruta concreta identifiquen modelo, proveedor, consumidor, contrato y evidencia de ejecución. No se atribuye esa capacidad a CatedralX por aparecer en la ilustración.

### Correspondencia interna de CatedralX: siete subsistemas

| Región conceptual | Anclaje técnico | Función y límite |
|---|---|---|
| Percepción sensorial — RSX | `elite/PERCEIVE/` | Captura, transporte y validación de observaciones; frescura y procedencia según el contrato de cada entrada |
| Córtex / razonamiento — SCX | `elite/REASON/` | Orquestación del análisis, contexto y razonamiento estructurado |
| Optimización — MCX | `elite/MCX/OPTIMIZE/` | Métricas y mecanismos complementarios de optimización |
| Regulación y defensa — DSX | `elite/DSX/DEFENSE/` | Guardas, límites, evaluación de riesgo y bloqueo defensivo |
| Decisión / acción potencial — AEX | `elite/AEX/` | Modela intención, riesgo y límites; el ejecutor es review-only y no crea ni ejecuta órdenes |
| Gobernanza y feedback — FEX | `elite/FEX/GOVERNANCE/` y `elite/FEX/FEEDBACK/` | Dominios separados: gobernanza económica y evaluación posterior de predicciones frente a outcomes observados |
| Procedencia — MSX | `elite/MSX/` | Registro de procedencia, secuencia y evidencia; no es memoria semántica general ni la CLI |

**ENERGY es infraestructura transversal de presupuesto computacional virtual; no es un octavo subsistema funcional.** Su implementación se distribuye entre `elite/ENERGY/` y el ledger `elite/MSX/energy_ledger.py`. La CLI canónica es `BIN/catedral`; no debe confundirse con MSX.

FEX separa explícitamente `GOVERNANCE/` y `FEEDBACK/`. `elite/FEX/trainer.py` se conserva como fachada de compatibilidad; su presencia no demuestra entrenamiento autónomo en producción.

## 3. Metabolismo energético: biomimetismo VRFB

La batería de flujo redox (VRFB) es una analogía visual para representar presupuesto, reservas y consumo de **créditos virtuales de cómputo**. No es una batería electroquímica ni mide energía física.

Anclajes localizados:
- `elite/ENERGY/virtual_vanadium_battery.py`: depósitos y contabilidad de créditos virtuales.
- `elite/ENERGY/resource_governor.py`: autoriza o rechaza consumo según saldo, reserva y descarga configurada.
- `elite/MSX/energy_ledger.py`: ledger JSONL append-only, con secuencia, cadena SHA-256, bloqueo y fsync.

Invariantes:
1. Los créditos representan unidades contables virtuales de cómputo; no joules, vatios-hora ni energía eléctrica.
2. El ciclo de razonamiento solicita presupuesto mediante el gobernador antes de continuar.
3. El saldo y las transacciones deben poder reconstruirse y conciliarse desde el ledger.
4. La cadena SHA-256 hace detectable una alteración de registros enlazados; no es firma digital, autenticación del productor ni anclaje externo independiente.
5. El ledger de energía no se confunde con `DecisionResult`, ledger de feedback ni ledger económico.
6. Corrupción o cadena rota deben fallar de forma cerrada según el contrato.

La ley de Poiseuille puede inspirar experimentos sobre capacidad, flujo y resistencia de colas, pero no hay que atribuirla literalmente al software. Cualquier modelo informático debe definir unidades propias, supuestos y validación empírica.

## 4. Córtex prefrontal: memoria, atención y predicción

La lámina organiza pasado, presente y futuro como una metáfora temporal. El código actual contiene piezas relacionadas, pero no acredita un único “córtex” ni una memoria cognitiva general:

| Dimensión visual | Anclaje comprobable en código/documentación | Límite |
|---|---|---|
| Pasado | MSX/provenance, stores y ledgers; estado endocrino persistido | Registros y estado no equivalen a memoria semántica general |
| Presente | PERCEIVE, REASON y guardas DSX | La ruta exacta depende del punto de entrada y caso de uso |
| Futuro | Predicciones registradas por FEX/FEEDBACK | Una predicción no es un outcome ni prueba de recompensa |
| Evaluación posterior | Outcomes observados por horizonte y fuente | Solo se etiqueta cuando el horizonte y las condiciones del contrato se cumplen |

`elite/REASON/free_energy.py` implementa una **heurística acotada de discrepancia/sorpresa predictiva** que compara una predicción de tendencia acotada con entradas observadas de mercado. El propio módulo declara que no es energía física, una probabilidad calibrada ni un objetivo completo de free energy variacional.

Por tanto, no se debe describir ese archivo como energía libre física ni asumir que calcula por sí solo el error TD de la lámina.

La expresión `delta_t = target_t - prediction_t` puede usarse como plantilla conceptual para un error de predicción, pero no se atribuye a una implementación concreta sin identificar productor, target, horizonte, escala, timestamp, fuente y pruebas.

## 5. Telemetría endocrina: estado modelado en REASON

A diferencia de otras etiquetas de la lámina, sí existe un `ProcesadorEndocrino` en `elite/REASON/procesador.py`. El código modela concentraciones numéricas acotadas y guarda el estado en el archivo configurado por `CATEDRALX_STATE_PATH` (por defecto, `~/.local/state/chalamandra/catedralx/hormonas.json`).

Las seis variables que aparecen en el código son:

| Variable de código | Estado que puede afirmarse |
|---|---|
| `oxitocina_O` | Concentración modelada entre 0 y 1 |
| `dopamina_D` | Concentración modelada entre 0 y 1 |
| `serotonina_S` | Concentración modelada entre 0 y 1 |
| `cortisol_C` | Concentración modelada entre 0 y 1; el guardado deriva `estres_critico` cuando supera 0.7 |
| `adrenalina_A` | Concentración modelada entre 0 y 1 |
| `melatonina_M` | Concentración modelada entre 0 y 1 |

El método `actualizar` usa entradas `sorpresa`, `gap` e `inercia` y parámetros de producción, decaimiento e interacción. `volcar_estado_quimico` obtiene esas entradas desde `percepcion_espacial` y persiste el estado.

**Corrección de la lámina:** GABA y endorfinas no aparecen entre las seis concentraciones de este procesador. Noradrenalina tampoco es el nombre de la variable implementada: el código usa adrenalina. No deben presentarse como telemetría implementada sin localizar otro productor y sus consumidores.

La integridad del archivo hormonal utiliza HMAC-SHA256 con keyring/clave configurada, escritura temporal, bloqueo y fsync. HMAC aporta verificación de integridad/autenticidad compartida bajo una clave; no es una firma Ed25519 ni una medición biológica. La presencia del código no prueba que el archivo exista o esté activo en una instalación concreta.

## 6. Eje HPA de seguridad: homeostasis como modelo conceptual

La etiqueta “Eje HPA” es biomimética. No se afirma que CatedralX implemente un eje endocrino fisiológico.

Sí hay controles de seguridad localizables, entre ellos:
- `elite/DSX/DEFENSE/defense.py`: evaluación de riesgo compuesto, presión de RAM y marcador global de pánico configurable por `CATEDRALX_PANIC_PATH`.
- `elite/DSX/DEFENSE/guardian_ram.py`: guardián versionado señalado por el mapa canónico.
- `elite/REASON/procesador.py`: estado endocrino modelado y umbral `estres_critico`.
- `elite/ENERGY/resource_governor.py`: control del presupuesto computacional virtual.
- `elite/AEX/ejecutor.py`: intención review-only; no crea órdenes ni ejecuta operaciones en vivo.

Ciclo conceptual de respuesta:
1. **Estímulo:** carga anómala, datos obsoletos, errores, corrupción o riesgo.
2. **Detección:** sensores y validadores que existan en la ruta concreta.
3. **Evaluación:** razonamiento y métricas, sujetos a las guardas.
4. **Veto/contención:** controles DSX, marcador de pánico y gobernador ENERGY.
5. **Recuperación:** solo mediante mecanismos concretos de reintento, conciliación e idempotencia acreditados para el flujo.
6. **Reanudación:** después de validar la condición de recuperación y la autorización exigida.

Homeostasis significa mantener invariantes y estados seguros, no permanecer siempre activo ni ocultar fallos. Ante incertidumbre crítica, la respuesta correcta puede ser bloquear. No se declara una recuperación automática universal.

## 7. Puente criptográfico y contratos entre sistemas

La frontera debe transportar identidad y evidencia de forma explícita, según el contrato de cada ruta:

- `trace_id` / `traceparent`: correlación de ejecución.
- `candidate_id`: identidad del candidato en Agents.
- `decision_id`: identificador usado por el contrato de aceptación de Agents.
- `evaluation_hash`: integridad del resultado de evaluación; no sustituye la procedencia del dato original.
- HMAC-SHA256 de Candidate Store y Ed25519 de aceptación son mecanismos distintos, con propósitos y dominios de confianza distintos.

Una firma o hash válido no demuestra corrección semántica, origen de datos, conveniencia económica ni autorización humana.

La aceptación independiente en Agents no equivale al estado `ACCEPTED` de una evaluación interna de CatedralX. Autorización humana, aceptación independiente, despacho y ejecución son etapas separadas. AEX en CatedralX es review-only y el código inspeccionado declara que live execution no está implementado.

## 8. Relación con Bernoulli Informacional

Bernoulli puede inspirar un balance de flujo y recursos, pero no es una ley física del software. La validación operativa debe usar métricas informáticas separadas:

- solicitudes recibidas y estados conciliados;
- throughput y latencia;
- CPU, memoria y créditos virtuales consumidos;
- errores, descartes y retrabajo;
- evidencia, verificación y aceptación independiente.

No se sumarán presión física, densidad física, velocidad de fluido o energía mecánica con métricas informáticas. Todo índice agregado debe declarar normalización, unidad, fuente, periodo y límites.

## 9. Criterios de conformidad arquitectónica

Una región de la lámina solo se considera implementada cuando se acredita:

1. módulo o servicio real y ruta versionada;
2. productor, consumidor y dirección de flujo;
3. contrato y esquema versionados;
4. propietario del estado y política de persistencia;
5. invariantes y comportamiento de fallo cerrado;
6. pruebas positivas, negativas, replay, concurrencia y recuperación cuando correspondan;
7. trazas o evidencia de runtime para afirmar que está activa;
8. CI asociado al SHA exacto para declarar validación automatizada.

Usar tres etiquetas en toda documentación y panel:
- **Implementado en código:** existe una ruta versionada y localizable.
- **Validado:** existe prueba o CI identificable en un SHA concreto, con alcance explícito.
- **Operativo:** existe evidencia de runtime del entorno y periodo concretos.

No inferir una etiqueta de otra.

## 10. Secuencia de trabajo propuesta

1. **Reconciliar:** comparar la visión con el árbol, los contratos y el grafo de dependencias.
2. **Cerrar contratos:** definir interfaces, productores y propietarios de señales/estados ambiguos.
3. **Instrumentar:** medir brechas justificadas, con unidades y fuentes.
4. **Validar:** pruebas de contrato, integridad, idempotencia, seguridad y recuperación.
5. **Integrar:** demostrar el flujo CatedralX → Agents → verificador con trazas correlacionadas.
6. **Operar:** evaluar telemetría real antes de afirmar homeostasis, eficiencia o escalabilidad.

## 11. Fuentes internas consultadas

- `docs/MAPA_SAGRADO.md`: topología, siete subsistemas, límites de CLI y flujos.
- `docs/CONTRATO_ARQUITECTONICO.md`: clasificación, tipos, responsabilidades y evidencia.
- `docs/GRAFO_DEPENDENCIAS_VERIFICADO.md`: relaciones estáticas, estado, pruebas y rutas de persistencia.
- `docs/ARQUITECTURA_CANONICA_CATEDRALX_AGENTS.md`: contrato de integración y brechas entre repositorios.
- `elite/REASON/procesador.py`: variables endocrinas, actualización y persistencia del estado.
- `elite/REASON/free_energy.py`: heurística acotada de discrepancia predictiva.
- `elite/ENERGY/virtual_vanadium_battery.py`, `elite/ENERGY/resource_governor.py` y `elite/MSX/energy_ledger.py`: presupuesto y ledger de créditos virtuales.
- `elite/DSX/DEFENSE/defense.py` y `elite/AEX/ejecutor.py`: controles defensivos e intención review-only.

**Alcance:** esta especificación define la arquitectura objetivo y sus criterios de prueba. No declara que todas las regiones de las láminas estén implementadas, conectadas o activas en runtime; tampoco autoriza ejecución financiera, despliegue ni cambios en Agents.
