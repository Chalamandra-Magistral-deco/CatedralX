# Contrato de arquitectura y clasificación — CatedralX

> **Propósito:** definir qué es cada elemento, de qué tipo es, dónde vive, qué responsabilidad posee y mediante qué contratos se conecta. Clasifica la arquitectura observada en esta rama; no convierte componentes existentes en capacidades operativas por decreto.

- Repositorio: Chalamandra-Magistral-deco/CatedralX
- Rama de referencia: fix/perceive-contract-hardening-20261122
- PR de trabajo: https://github.com/Chalamandra-Magistral-deco/CatedralX/pull/64
- Estado: especificación documental en revisión.

## 1. Regla de clasificación

Todo elemento arquitectónico debe declarar:

| Campo | Definición |
|---|---|
| Identidad | Nombre estable dentro de su ámbito |
| Tipo | Sistema, subsistema, módulo, interfaz, contrato, dato, proceso, política, almacenamiento, evidencia o documentación |
| Ubicación | Ruta versionada, ruta externa de estado o servicio externo |
| Responsabilidad | Responsabilidad primaria y límites explícitos |
| Entradas/salidas | Datos y contratos que acepta y produce |
| Relaciones | Dependencias y dirección de comunicación |
| Evidencia | Qué prueba existencia, implementación, integración, prueba, despliegue o aceptación |

**Regla:** el nombre de un directorio, clase o concepto no demuestra integración, ejecución, despliegue, autorización ni aceptación.

## 2. Niveles que no deben mezclarse

| Nivel | Qué representa | Ejemplo | No confundir con |
|---|---|---|---|
| Ecosistema | Sistemas independientes que colaboran | Usuario/producto, API, Agents, CatedralX y distribución | Paquete Python |
| Sistema | Unidad de software con propósito y límites propios | CatedralX | Subsistema interno |
| Subsistema | Dominio funcional con responsabilidad delimitada | PERCEIVE, REASON, MCX, DSX, AEX, FEX, MSX | Archivo individual |
| Infraestructura transversal | Capacidad interna compartida | ENERGY, contratos | Octavo subsistema funcional |
| Módulo | Archivo o paquete implementable | elite/REASON/orchestrator.py | Toda la responsabilidad de REASON |
| Componente | Clase, función o unidad interna | Validador, constructor, gobernador | Contrato de integración |
| Contrato | Acuerdo verificable de estructura, semántica e invariantes | JSON Schema de DecisionResult | Implementación o resultado |
| Dato/estado | Información transportada o persistida | Snapshot, estado, ledger | Proceso que lo modifica |
| Proceso/flujo | Secuencia de pasos y transiciones | Ciclo one-shot | Módulo o directorio |
| Política/guarda | Restricción que permite, limita o bloquea | Guardas DSX, límites de riesgo | Decisión financiera |
| Evidencia | Registro que permite verificar una afirmación | Test, traza, hash, CI, aceptación | Afirmación misma |
| Documentación | Descripción humana de diseño/uso | docs/MAPA_SAGRADO.md | Fuente de verdad del comportamiento |

## 3. Catálogo de subsistemas funcionales

Los siete subsistemas se clasifican por responsabilidad, no por analogía biológica.

| Identidad | Tipo | Ubicación canónica | Responsabilidad | No debe hacer |
|---|---|---|---|---|
| RSX / PERCEIVE | Subsistema de percepción e ingesta | elite/PERCEIVE/ | Capturar, transportar, validar y describir observaciones; controlar frescura y procedencia | Inferir decisiones financieras o ejecutar acciones |
| SCX / REASON | Subsistema de razonamiento/orquestación cognitiva | elite/REASON/ | Coordinar análisis, construir contexto y producir razonamiento/resultados intermedios | Convertir hipótesis en órdenes o saltarse guardas |
| MCX / OPTIMIZE | Subsistema de optimización y métricas | elite/MCX/ | Calcular métricas, diagnósticos y optimización; evaluar resultados observados con contrato válido | Fabricar resultados realizados desde predicciones o autorizar acciones |
| DSX / DEFENSE | Subsistema de defensa y restricciones | elite/DSX/DEFENSE/ | Aplicar guardas, límites, integridad y bloqueos | Alterar silenciosamente el origen o actuar como motor de decisión económica |
| AEX / DECISION | Subsistema de decisión, riesgo e intención de acción | elite/AEX/ | Modelar decisiones potenciales, riesgo, límites y acciones sujetas a autorización | Suponer que buy/sell/hold equivale a orden autorizada o ejecutada |
| FEX / GOVERNANCE + FEEDBACK | Subsistema de gobernanza y evaluación posterior | elite/FEX/GOVERNANCE/ y elite/FEX/FEEDBACK/ | Gestionar gobernanza económica, feedback y evaluación supervisada/offline | Tratar predicciones no verificadas como outcomes observados |
| MSX / PROVENANCE | Subsistema de procedencia y registros | elite/MSX/ | Registrar procedencia, secuencia y evidencia asociada | Ser la CLI, interfaz de usuario o motor de decisión |

### Ubicaciones específicas

- elite/MSX/provenance.py: registro de procedencia.
- elite/MSX/energy_ledger.py: ledger append-only con cadena hash; no es memoria semántica general ni firma criptográfica.
- elite/ENERGY/virtual_vanadium_battery.py: contabilidad de créditos virtuales en depósitos operativo y adaptativo.
- elite/ENERGY/resource_governor.py: autorización y control de consumo de créditos virtuales.
- elite/contracts/: normalización, construcción y persistencia de resultados estructurados.
- elite/contracts/schemas/: esquemas JSON versionados.
- BIN/catedral: ejecutable canónico de CLI.
- elite/bin/: adaptadores y comandos one-shot invocados por la CLI.
- tests/: pruebas automatizadas; no son runtime productivo.
- docs/: especificaciones y guías; no ejecutan el sistema.

**Corrección de clasificación:** CLI no es MSX. La CLI es una interfaz de operación separada; MSX se limita a procedencia y registro.

## 4. Infraestructura transversal y contratos

| Elemento | Tipo | Ubicación | Función | Relación |
|---|---|---|---|---|
| ENERGY | Infraestructura transversal de presupuesto computacional virtual | elite/ENERGY/ | Administrar capacidad, saldo, descarga, reservas y autorización de créditos virtuales | Procesos autorizados solicitan presupuesto; MSX conserva el ledger |
| Virtual Vanadium Battery | Modelo contable de recursos virtuales | elite/ENERGY/virtual_vanadium_battery.py | Representar depósitos operativo/adaptativo, límites y transacciones | Gobernada por resource_governor |
| Resource Governor | Política/servicio interno de autorización | elite/ENERGY/resource_governor.py | Autorizar o rechazar consumo según saldo, reserva y descarga | Consulta/escribe el ledger MSX |
| Energy Ledger | Almacenamiento durable append-only | elite/MSX/energy_ledger.py | Registrar transacciones con secuencia y cadena SHA-256 | Permite reconstruir/verificar contabilidad; no equivale a firma digital |
| Contracts | Capa transversal de contratos | elite/contracts/ | Normalizar acciones y construir/persistir resultados tipados | Define límites entre productores y consumidores |
| DecisionResult | Tipo de resultado estructurado | elite/contracts/schemas/decision_result.json | Transportar resultado analítico y metadatos bajo esquema | No es orden, ejecución ni aceptación externa |

Los créditos de ENERGY son **unidades contables de cómputo virtual**, no joules, electricidad, potencia física ni una batería electroquímica real.

## 5. Tipos de datos y estados

- **Observación:** dato externo capturado por PERCEIVE; conserva fuente, timestamp, unidad, frescura y validación.
- **Snapshot:** representación de observación/estado en un instante; no es memoria histórica por sí solo.
- **Estado:** datos mutables para continuar un proceso; su dueño y política de persistencia se declaran aparte.
- **Predicción:** afirmación prospectiva con identificador y horizonte; no es resultado observado.
- **Outcome:** resultado medido ex post contra observación posterior válida; no se infiere de la predicción.
- **DecisionResult:** objeto tipado que expresa un resultado analítico; no implica aceptación.
- **Candidato:** resultado propuesto para revisión; no equivale a aceptado.
- **Aceptación:** decisión explícita de autoridad/verificador definido, con identidad, alcance y evidencia.
- **Orden:** instrucción externa con semántica de ejecución; requiere autorización independiente y no deriva de buy/sell/hold.
- **Ejecución:** efecto comprobable en sistema externo; requiere confirmación externa y registro.
- **Ledger:** registro secuencial de transacciones/eventos; no es base de conocimiento general.
- **Traza:** correlación temporal de spans/eventos; no reemplaza ledger ni aceptación.

Esquemas de resultado versionados en esta rama:
- elite/contracts/schemas/chalamandra_contract.json
- elite/contracts/schemas/decision_result.json
- elite/contracts/schemas/economic_opportunity_result.json

La validez sintáctica de JSON Schema no demuestra que todos los productores y consumidores estén integrados ni que respeten el contrato en runtime.

## 6. Relaciones y dirección de flujo

### 6.1 Flujo lógico interno de referencia

```text
Observaciones
    |
    v
RSX / PERCEIVE -- datos validados y procedencia de origen
    |
    v
SCX / REASON ---- contexto, análisis y resultado intermedio
    |---- MCX / OPTIMIZE (métricas y diagnósticos)
    |---- DSX / DEFENSE (guardas y bloqueos)
    v
AEX / DECISION -- decisión potencial, riesgo y límites
    |
    v
CONTRACTS ------- DecisionResult tipado
    |---- FEX / FEEDBACK (evaluación posterior con outcomes observados)
    |---- MSX / PROVENANCE (registro y trazabilidad)

ENERGY ---------- presupuesto transversal solicitado por procesos autorizados
```

Es un mapa de responsabilidades y relaciones lógicas. El orden exacto de invocación depende del caso de uso y debe verificarse en entrypoints, llamadas y pruebas. No se afirma que los siete subsistemas se invoquen en cada ciclo.

### 6.2 Flujos de integración del ecosistema

| Flujo | Nivel | Dirección | Evidencia necesaria para declararlo integrado |
|---|---|---|---|
| Normal | Ecosistema | Usuario/producto → API/Agents → CatedralX → candidato/evidencia | Configuración real, contrato compartido, trace_id correlacionado y prueba end-to-end |
| Inverso | Ecosistema | Candidato → verificador independiente → aceptación → distribución autorizada | Identidad del verificador, evidencia, decisión de aceptación y autorización |
| Invertido/autónomo | Ecosistema | Evento/condición autorizada → orquestación → Agents/CatedralX → evidencia/verificación | Disparador autorizado, límites, idempotencia, trazas y control de salida |

Su presencia documental no prueba que API, Agents, distribución o verificador estén conectados o desplegados. No atribuir integraciones externas a este repositorio sin configuración y evidencia.

## 7. Modelos conceptuales: Mente Tiempo y mente bicameral

### Mente Tiempo

Es un **modelo de organización temporal del aprendizaje**, no un subsistema independiente ni una afirmación neurobiológica.

| Dimensión | Función conceptual | Anclaje técnico | Límite |
|---|---|---|---|
| Pasado | Conservar experiencias y procedencia | MSX, registros y stores persistentes | Un ledger no es memoria semántica completa |
| Presente | Procesar señales y contexto actual | PERCEIVE + REASON + guardas DSX | Solo está activo lo que ejecuta el caso de uso |
| Futuro | Formular predicciones y evaluar discrepancias | Predicciones y evaluación ex post en FEX/MCX | free_energy.py no es energía física ni demuestra por sí solo planificación |
| Actualización | Incorporar outcomes verificados | Feedback validado y políticas de actualización | No aprender de outcomes hipotéticos |

Ciclo conceptual: PASADO → PRESENTE → PREDICCIÓN → OBSERVACIÓN POSTERIOR → EVALUACIÓN → ACTUALIZACIÓN. Solo se consolida feedback cuando el outcome está observado y validado.

### Mente bicameral

Patrón de deliberación con dos funciones: generación de hipótesis y crítica/verificación independiente. **No se clasifica como subsistema implementado** hasta que existan módulos, contratos, pruebas y trazas que acrediten ambas funciones y la resolución de desacuerdos mediante evidencia.

## 8. Principios de corrección antierror

| Principio | Regla verificable | Error que previene | Evidencia mínima |
|---|---|---|---|
| Separación de niveles | Cada elemento declara un nivel primario y sus relaciones | Llamar subsistema a un archivo o contrato | Catálogo y revisión de dependencias |
| Responsabilidad única | Cada módulo declara responsabilidad y límites | Duplicación y acoplamiento accidental | Tests unitarios y revisión de imports |
| Contrato antes de conexión | Productor y consumidor validan el mismo esquema/versión | Payloads incompatibles | Pruebas de contrato en ambos extremos |
| Dirección explícita | Cada relación declara productor, consumidor y dirección | Ciclos ocultos y dependencias inversas | Grafo de dependencias y tests |
| Dato no es decisión | Observación, predicción, outcome, decisión, candidato, aceptación y orden son tipos distintos | Ejecutar/aprender desde señal no verificada | Esquemas y pruebas negativas |
| Evidencia no es afirmación | Cada estado declarado enlaza evidencia reproducible | Afirmar integrado/probado/desplegado sin prueba | CI del SHA, trazas, configuración, registros |
| Analogía no es implementación | Metáfora traducida a mecanismo, invariante y test | Atribuir capacidades inexistentes | Matriz metáfora → mecanismo → invariante → test |
| Fallo cerrado | Datos, firmas, presupuesto o autorización inválidos bloquean transición | Continuar con estado desconocido | Pruebas de rechazo y ausencia de efectos |
| Persistencia explícita | Estado declara dueño, formato, ruta, retención y recuperación | Confundir snapshot, memoria y ledger | Pruebas de reinicio, integridad y recuperación |
| Idempotencia | Reintentos con misma identidad no duplican efectos | Doble gasto, feedback o despacho | Pruebas replay/concurrencia |
| Sin autoridad implícita | Ningún subsistema obtiene permisos por existir o producir resultado | Acción externa sin aprobación | Pruebas de no ejecución sin autorización |
| Estado por commit | CI y revisión se vinculan al SHA exacto | Heredar un verde antiguo a código nuevo | Checks del commit y artefactos |

## 9. Vocabulario de estado obligatorio

- **Existe:** hay archivo, módulo, servicio o configuración identificable.
- **Implementado:** hay comportamiento en código para una función delimitada.
- **Conectado:** existe relación ejecutable entre productor y consumidor.
- **Integrado:** el flujo conjunto funciona bajo contrato compartido y prueba de integración.
- **Probado:** una prueba identificada se ejecutó y su resultado está disponible.
- **Desplegado:** existe artefacto instalado en un entorno identificado.
- **Activo:** la instancia está ejecutándose y responde en el momento medido.
- **Aceptado:** autoridad definida aprobó el resultado con evidencia.
- **Ejecutado:** el efecto externo está confirmado por el sistema destinatario.

Nunca usar estos términos como sinónimos.

## 10. Fuente de verdad y mantenimiento

1. Árbol Git del SHA consultado: existencia y rutas.
2. Código ejecutable: comportamiento implementado.
3. Esquemas y contratos: estructura y semántica acordada.
4. Pruebas/CI del SHA exacto: comportamiento verificado en ese alcance.
5. Configuración y trazas: integración, despliegue y actividad.
6. Registro del verificador: aceptación.
7. Documentación: definición y navegación; no sustituye las evidencias anteriores.

Todo cambio de ruta, tipo, responsabilidad o relación debe actualizar este catálogo y sus pruebas. Lo no demostrado se etiqueta como **objetivo**, **pendiente** o **no verificado**, nunca como implementación.
