# Arquitectura Ciber-Biológica de CatedralX

> **Estado:** especificación arquitectónica objetivo, derivada de las láminas de referencia aportadas por la propietaria del proyecto. No certifica que todos los mecanismos estén implementados, conectados o activos en runtime.
>
> **Regla de diseño:** la biomimética organiza responsabilidades y preguntas de ingeniería; no convierte una analogía biológica en una capacidad de software ni en evidencia de funcionamiento.

## 1. Visión: dos continentes y un puente criptográfico

La arquitectura se representa como dos dominios autónomos:

- **Continente interior — CatedralX:** percepción validada, razonamiento determinista, optimización, defensa, decisión potencial, procedencia y gobernanza.
- **Continente exterior — Agents:** admisión y coordinación de tareas, invocación del motor, persistencia de candidatos, verificación independiente y distribución condicionada.

El **Puente Criptográfico** es el conjunto de contratos, identificadores, evidencias y verificaciones que permite intercambiar resultados entre ambos dominios. No es un microservicio ni concede autoridad por sí mismo.

Frontera mínima:
1. Agents entrega una solicitud conforme al contrato.
2. CatedralX valida entradas y produce un `DecisionResult` tipado con procedencia.
3. Agents conserva el candidato y lo somete a verificación independiente.
4. Aceptación, autorización humana, despacho y ejecución siguen siendo etapas distintas.
5. Ninguna salida de CatedralX se interpreta automáticamente como orden ejecutable.

## 2. Mente bicameral: separación de responsabilidades

La imagen de dos hemisferios expresa una división funcional, no una afirmación neuroanatómica.

| Dominio visual | Sistema | Responsabilidad técnica | Límites |
|---|---|---|---|
| Hemisferio de precisión | CatedralX | Validar observaciones, razonar, calcular métricas, aplicar guardas y producir resultados estructurados | No coordina la cola externa ni se autoautoriza para ejecutar |
| Hemisferio de acción | Agents | Admitir, coordinar, invocar, persistir candidatos, verificar y distribuir bajo autorización | No suplanta el razonamiento financiero ni inventa métricas upstream |

### Correspondencia interna de CatedralX

| Región conceptual | Anclaje técnico existente | Función que debe preservarse |
|---|---|---|
| Percepción sensorial | `elite/PERCEIVE/` (RSX) | Captura, validación, frescura y procedencia de observaciones |
| Córtex / razonamiento | `elite/REASON/` (SCX) | Contexto, orquestación, razonamiento y resultados intermedios |
| Regulación y defensa | `elite/DSX/DEFENSE/` | Guardas, veto, límites, integridad y fallo cerrado |
| Optimización | `elite/MCX/OPTIMIZE/` | Métricas, evaluación y optimización con outcomes válidos |
| Decisión potencial | `elite/AEX/` | Intención, riesgo y límites; no equivale a autorización ni ejecución |
| Gobernanza y aprendizaje | `elite/FEX/` | Gobernanza, feedback y evaluación ex post supervisada |
| Memoria de procedencia | `elite/MSX/` | Secuencia, trazabilidad y evidencia; no es memoria semántica general |
| Metabolismo de recursos | `elite/ENERGY/` + ledger en `elite/MSX/energy_ledger.py` | Presupuesto computacional virtual y contabilidad durable |

ENERGY es infraestructura transversal, no un octavo subsistema funcional. La CLI es una interfaz de operación separada; no debe confundirse con MSX.

## 3. Metabolismo energético: biomimetismo VRFB

La batería de flujo redox es un modelo conceptual para representar presupuesto y reservas computacionales.

Anclajes técnicos:
- `elite/ENERGY/virtual_vanadium_battery.py`: depósitos y créditos virtuales.
- `elite/ENERGY/resource_governor.py`: autorización o rechazo del consumo.
- `elite/MSX/energy_ledger.py`: registro append-only de transacciones y cadena hash.

Invariantes:
1. Los créditos representan **unidades contables virtuales de cómputo**, no energía eléctrica, joules ni una batería electroquímica real.
2. Un proceso consume presupuesto solo después de superar las reglas del gobernador.
3. El saldo, las reservas, los límites y las transacciones deben poder conciliarse.
4. El ledger de energía no se confunde con DecisionResult, ledger económico ni feedback.
5. La falta de saldo, la corrupción o un estado desconocido deben bloquear el consumo cuando así lo exige el contrato.

La analogía de la ley de Poiseuille puede orientar experimentos de capacidad, flujo y resistencia de colas, pero solo después de definir métricas informáticas con unidades propias. No se debe presentar como una ley física aplicada literalmente al software.

## 4. Córtex prefrontal: pasado, presente y futuro

La organización temporal se representa como un ciclo verificable:

| Dimensión | Anclaje | Significado |
|---|---|---|
| Pasado | MSX, stores y ledgers | Conservar registros, procedencia y resultados observados |
| Presente | PERCEIVE + REASON + guardas DSX | Validar y procesar el contexto actual |
| Futuro | Predicciones y evaluación en MCX/FEX | Formular hipótesis y medirlas contra outcomes posteriores |
| Actualización | FEX/feedback validado | Aprender solo de resultados observados, identificables y con horizonte cumplido |

Error de predicción:
`delta_t = target_t - prediction_t`

Esta expresión es una plantilla conceptual. La definición operativa debe fijar target, predicción, escala, horizonte, timestamp y fuente. No se debe actualizar el modelo a partir de predicciones no verificadas ni tratar `free_energy.py` como energía física.

## 5. Telemetría endocrina: señales de regulación

Los nombres GABA, dopamina, cortisol y endorfinas son etiquetas biomiméticas para estados de control de software, no sustancias presentes en el sistema.

| Etiqueta visual | Interpretación informática propuesta | Control que debe observarse |
|---|---|---|
| GABA — freno | Restricción, veto o limitación | DSX, guardas, límites y bloqueo |
| Dopamina — futuro | Señal de recompensa/aprendizaje | Predicción frente a outcome observado |
| Cortisol — alarma | Señal de estrés o riesgo operativo | Alertas, errores, volatilidad de carga y pánico |
| Endorfinas — tolerancia | Recuperación y tolerancia a fallos | Reintentos acotados, circuit breakers y recuperación verificada |

No se afirmará que existe un indicador dinámico hasta localizar su productor, fórmula, unidad, persistencia, consumidor y pruebas. Los campos ausentes deben mostrarse como no medidos, nunca inferirse de una etiqueta.

## 6. Eje HPA de seguridad: homeostasis bajo estrés

El modelo de seguridad debe responder a perturbaciones sin perder control:

1. **Estímulo:** carga anómala, datos obsoletos, errores, corrupción, incertidumbre o riesgo.
2. **Detección:** PERCEIVE, telemetría disponible y validadores.
3. **Evaluación:** REASON y MCX, sin saltarse las guardas.
4. **Veto y contención:** DSX, marcador de pánico, límites y gobernador ENERGY.
5. **Recuperación:** reintentos idempotentes y acotados, conciliación de estado y evidencia.
6. **Reanudación:** solo después de validar la condición de recuperación y la autorización exigida.

Homeostasis significa mantener invariantes y estados seguros, no permanecer siempre activo ni ocultar fallos. Ante incertidumbre crítica, la respuesta correcta puede ser bloquear.

## 7. Puente criptográfico y contratos entre sistemas

La frontera debe transportar identidad y evidencia de forma explícita:

- `trace_id` / `traceparent`: correlación temporal de la ejecución.
- `candidate_id`: identidad del candidato en Agents.
- `decision_id`: identificador de la decisión usada por el contrato de aceptación.
- `evaluation_hash`: integridad del resultado de evaluación; no sustituye la procedencia del dato original.
- Firmas y verificaciones: autentican una identidad o integridad dentro de una política de confianza; no demuestran por sí solas corrección semántica o conveniencia económica.

La aceptación independiente en Agents no es equivalente al estado `ACCEPTED` de una evaluación interna de CatedralX. Autorización humana, aceptación, despacho y ejecución son estados separados.

## 8. Relación con Bernoulli Informacional

Bernoulli puede utilizarse como inspiración para diseñar un balance de flujo y recursos, pero no como ley física del software. La validación operativa debe usar magnitudes informáticas independientes:

- solicitudes recibidas y estados conciliados;
- throughput y latencia;
- consumo de CPU, memoria y créditos virtuales;
- errores, descartes y retrabajo;
- evidencia, verificación y tasa de aceptación independiente.

No se sumarán presión física, densidad física, velocidad de fluido o energía mecánica con métricas informáticas. Cualquier índice agregado debe definir normalización, unidad, fuente y límites.

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

## 10. Secuencia de trabajo propuesta

1. **Reconciliar:** comparar esta visión con el árbol y los contratos reales, sin cambiar comportamiento.
2. **Cerrar contratos:** definir las interfaces y propietarios de señales/estados aún ambiguos.
3. **Instrumentar:** medir únicamente brechas justificadas y conservar unidades/fuentes.
4. **Validar:** añadir pruebas de contrato, integridad, idempotencia, seguridad y recuperación.
5. **Integrar:** demostrar el flujo CatedralX → Agents → verificador con trazas correlacionadas.
6. **Operar:** evaluar telemetría real antes de afirmar homeostasis, eficiencia o escalabilidad.

## 11. Fuentes internas

- `CONTRATO_ARQUITECTONICO.md`: taxonomía, límites y principios antierror.
- `MAPA_SAGRADO.md`: topología canónica del repositorio.
- `GRAFO_DEPENDENCIAS_VERIFICADO.md`: llamadas, estado y pruebas identificadas estáticamente.
- `ARQUITECTURA_CANONICA_CATEDRALX_AGENTS.md`: contrato de integración entre ambos repositorios.

**Alcance de esta especificación:** define la forma objetivo de la arquitectura y sus criterios de prueba. No declara que las seis láminas estén implementadas en código ni autoriza ejecución financiera, despliegue o cambios en Agents.
