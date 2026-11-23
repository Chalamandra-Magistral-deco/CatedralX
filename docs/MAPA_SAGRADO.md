# MAPA SAGRADO — Arquitectura canónica de CatedralX

> **Principio rector:** lo que ejecuta vive en la raíz o en los módulos de `elite/`; lo que explica vive en `docs/`. La arquitectura se describe según el código versionado, no según aspiraciones ni analogías.

## 1. Identidad del sistema

CatedralX es un motor de razonamiento y análisis financiero experimental. Recibe observaciones, valida su integridad, procesa el contexto mediante módulos especializados y produce resultados estructurados que pueden conservarse y verificarse.

No es un chatbot. La existencia de módulos de decisión o de despacho no significa que el sistema esté autorizado para operar capital. La configuración CLI/Docker documentada actualmente es de ejecución puntual; no constituye por sí misma un servicio HTTP persistente.

## 2. Topología del repositorio

```text
CatedralX/
├── .github/workflows/       # Integración continua
├── BIN/                     # Entrada CLI canónica: catedral
├── deploy/systemd/          # Ejemplos de unidades de servicio y timer
├── elite/
│   ├── PERCEIVE/            # RSX: percepción e ingesta
│   ├── REASON/              # SCX: razonamiento y ciclo cognitivo
│   ├── MCX/OPTIMIZE/        # Optimización y métricas complementarias
│   ├── DSX/DEFENSE/         # Defensa, guardas y límites
│   ├── AEX/                 # Decisión, riesgo y acciones
│   ├── FEX/                 # Gobernanza, feedback y evaluación
│   ├── MSX/                 # Procedencia y registro
│   ├── contracts/           # Contratos, construcción y persistencia de resultados
│   └── bin/                 # Adaptadores y herramientas operativas invocadas por CLI
├── scripts/                 # Herramientas de análisis, backtesting y seguridad
├── tests/                   # Pruebas automatizadas
├── docs/                    # Documentación arquitectónica y guías
├── Dockerfile               # Imagen CLI puntual
├── docker-compose.yml       # Ejecución puntual de la imagen
├── pyproject.toml           # Metadatos, dependencias y configuración pytest
├── requirements.txt         # Rangos compatibles de runtime
├── requirements-lock.txt    # Versiones exactas para instalación general/CI
└── requirements-runtime.lock # Versiones exactas instaladas en la imagen Docker
```

Esta topología refleja el árbol Git inspeccionado en la rama `fix/perceive-contract-hardening-20261122`. No implica que cada módulo esté activo en todos los flujos de ejecución.

## 3. Los siete subsistemas y sus fronteras

| Subsistema | Ruta real | Responsabilidad arquitectónica |
|---|---|---|
| RSX — Percepción | `elite/PERCEIVE/` | Capturar, transportar y validar observaciones y datos de entrada |
| SCX — Razonamiento | `elite/REASON/` | Orquestar el análisis, mantener contexto cognitivo y producir razonamiento estructurado |
| MCX — Optimización | `elite/MCX/OPTIMIZE/` | Proveer métricas y mecanismos complementarios de optimización |
| DSX — Defensa | `elite/DSX/DEFENSE/` | Aplicar guardas, límites y controles defensivos |
| AEX — Acción/decisión | `elite/AEX/` | Modelar decisiones, riesgo, límites y operaciones potenciales |
| FEX — Feedback/gobernanza | `elite/FEX/` | Gobernanza económica, retroalimentación y evaluación supervisada/offline |
| MSX — Interfaz/procedencia | `elite/MSX/` y `elite/bin/` | Exponer adaptadores de operación y registrar procedencia; la CLI vive en `BIN/` y `elite/bin/` |

**Frontera importante:** los nombres de los subsistemas expresan responsabilidades. No deben interpretarse como prueba de que exista una integración completa, una llamada en runtime o un despliegue independiente.

### Ubicaciones que no deben confundirse

- El ejecutable público de la CLI es `BIN/catedral`.
- Los adaptadores invocados por la CLI están en `elite/bin/` (por ejemplo, `nexus.py`, `feed_once.py`, `impact_cycle.py`, `dispatch_agents.py` y `user_feedback.py`).
- `elite/MSX/provenance.py` registra procedencia; no es el ejecutable de la CLI.
- El guardián versionado es `elite/DSX/DEFENSE/guardian_ram.py`; no se debe documentar un `guardian.py` inexistente.
- FEX separa `GOVERNANCE/` y `FEEDBACK/`. `elite/FEX/trainer.py` se conserva como fachada de compatibilidad.
- Los contratos de resultado están en `elite/contracts/`; sus esquemas JSON están en `elite/contracts/schemas/`.

## 4. Flujo interno de referencia

```text
Observaciones / datos de entrada
            │
            ▼
RSX — PERCEIVE
captura · transporte · validación
            │
            ▼
SCX — REASON
contexto · análisis · razonamiento
            │
            ├──────── MCX — OPTIMIZE
            │          métricas complementarias
            │
            ├──────── DSX — DEFENSE
            │          guardas y restricciones
            │
            ▼
AEX — DECISION
evaluación de decisión · riesgo · límites
            │
            ▼
CONTRACTS
normalización · DecisionResult · persistencia
            │
            ▼
FEX — GOVERNANCE / FEEDBACK
evaluación posterior · feedback supervisado
            │
            ▼
MSX / CLI
presentación · adaptadores · procedencia
```

El diagrama expresa las responsabilidades y el flujo lógico de referencia. Las dependencias y el orden exacto de llamadas deben comprobarse en los puntos de entrada y pruebas de cada caso de uso; no se afirma que todos los subsistemas se invoquen en cada ejecución.

## 5. Contratos y persistencia

La capa `elite/contracts/` concentra:

- `actions.py`: normalización de acciones.
- `builder.py`: construcción de resultados estructurados.
- `result_store.py`: persistencia append-only de resultados.
- `schemas/`: esquemas JSON versionados, entre ellos `chalamandra_contract.json`, `decision_result.json` y `economic_opportunity_result.json`.

Las rutas de estado se configuran mediante variables de entorno y, por defecto, se mantienen fuera del checkout:

| Dato | Variable | Ruta predeterminada |
|---|---|---|
| Snapshot RSX | `CATEDRALX_SNAPSHOT_PATH` | `/dev/shm/cathedral_snapshot.json` |
| Estado | `CATEDRALX_STATE_PATH` | `~/.local/state/chalamandra/catedralx/hormonas.json` |
| Feedback de usuario | `CATEDRALX_USER_FEEDBACK_PATH` | `~/.local/state/chalamandra/catedralx/user_feedback.jsonl` |
| Resultados | `CATEDRALX_RESULT_STORE_PATH` | `~/.local/state/chalamandra/catedralx/results.jsonl` |

Los valores predeterminados deben contrastarse con la configuración efectiva del entorno antes de diagnosticar una instalación concreta.

## 6. Tres flujos de integración del ecosistema

La arquitectura de integración contempla tres direcciones conceptuales:

1. **Flujo normal:** usuario/producto → API o Agents → CatedralX → resultado candidato y evidencia.
2. **Flujo inverso:** resultado candidato → verificación independiente → aceptación → distribución autorizada.
3. **Flujo invertido:** evento o condición autorizada → orquestación → Agents/CatedralX → evidencia y verificación.

Estos tres flujos describen la topología objetivo del ecosistema. Este repositorio, por sí solo, no demuestra que API, Agents, aceptación y distribución estén desplegados, conectados y operativos de extremo a extremo. La integración debe acreditarse con configuración, trazas y pruebas de contrato.

## 7. Entrada, ejecución y empaquetado

- `BIN/catedral` enruta los comandos de la CLI a módulos Python.
- `Dockerfile` construye una imagen que instala `requirements-runtime.lock`, copia `elite/` y `BIN/`, y ejecuta por defecto `catedral status`.
- `docker-compose.yml` declara una ejecución puntual del contenedor y un volumen local para estado; no publica un puerto HTTP.
- `deploy/systemd/` contiene ejemplos de unidades de servicio y timer; su presencia no significa que estén instalados o habilitados en un host.
- `.github/workflows/catedralx-tests.yml` automatiza instalación, validaciones, pruebas, compilación, build/smoke test Docker y escaneo de secretos. El workflow no implementa despliegue continuo.

## 8. CI, pruebas y evidencia

La existencia de pruebas y workflows no equivale a una ejecución exitosa. Para declarar una validación aprobada se requiere consultar el resultado de ejecución correspondiente al commit exacto y revisar sus artefactos y logs.

El workflow actual comprueba los esquemas JSON versionados, ejecuta pytest, compila fuentes Python, valida Compose, construye la imagen y ejecuta su comando predeterminado. También realiza escaneo histórico de secretos con Gitleaks.

## 9. Límites de seguridad y operación

- Una etiqueta analítica `buy`, `sell` o `hold` no es una orden ni una recomendación de inversión.
- No se debe inferir ejecución de órdenes por la existencia de módulos AEX o de adaptadores de despacho.
- Ningún flujo externo debe considerarse autorizado sin evidencia de autenticación, autorización, validación y aceptación.
- La ejecución real, la integración con Agents/API y el despliegue deben documentarse por separado y con pruebas observables.
- Los datos operativos, secretos, snapshots y artefactos temporales no deben incorporarse al repositorio.

## 10. Fuente de verdad y mantenimiento

1. El árbol Git del commit revisado es la fuente para rutas y existencia de archivos.
2. El código y las pruebas son la fuente para comportamiento implementado.
3. Los workflows y sus ejecuciones son la fuente para el estado de CI.
4. La configuración efectiva y las trazas son la fuente para integraciones y despliegues.
5. Los documentos de arquitectura describen responsabilidades y objetivos, pero no sustituyen evidencia de ejecución.

**Nota sobre `MAPA_SAGRADO.json`:** existe en la raíz como snapshot estructural histórico, anclado a un commit anterior de `main`. Sus conteos y referencias no deben presentarse como inventario actualizado de esta rama. Este documento Markdown describe la topología inspeccionada en la rama de trabajo; ambos archivos tienen propósitos y fechas de referencia distintos.
