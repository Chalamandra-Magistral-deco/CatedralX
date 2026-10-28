# Comparación del clon y el repositorio principal — 2026-10-24

## Dictamen

**Resultado: divergencia de árboles de trabajo; no integrar todavía.**  
La comparación fue de solo lectura. No se editaron archivos del repositorio principal, no se copiaron cambios, no hubo commit/push/merge/deploy.

## Identidad y base de comparación

- Repositorio principal: `/home/azureuser/workspace/repos/CatedralX`
- Clon de revisión: `/home/azureuser/workspace/repos/CatedralX-verify`
- Rama del principal: `feat/financial-motor-deterministic`
- El `HEAD` del principal es la base común detectada del clon; `git diff main-HEAD...clone-HEAD` no mostró cambios comprometidos entre las puntas comparadas. La divergencia examinada está en los árboles de trabajo no comprometidos.
- Estado de trabajo informado: principal con 14 entradas; clon con 34 entradas. Los conteos incluyen modificaciones y archivos no rastreados.

## Hallazgos

### 1. Archivos existentes en ambos con contenido distinto

Hay **16 rutas compartidas con contenido distinto** al comparar los árboles de trabajo. Entre las zonas de mayor riesgo están:

- `elite/AEX/DECISION/ordenes.py`
- `elite/REASON/orchestrator.py`
- `elite/REASON/razon.py`
- `elite/REASON/schemas.py`
- `elite/DSX/DEFENSE/defense.py`
- `elite/FEX/GOVERNANCE/__init__.py`
- `elite/PERCEIVE/bunker.py`
- `elite/AEX/DECISION/operador.py`
- `elite/FEX/trainer.py`
- `tests/test_financial_engine.py`

También difieren `BIN/catedral`, `README.md`, `elite/AEX/ejecutor.py`, `elite/PERCEIVE/percepcion.py`, `elite/FEX/FEEDBACK/feedback_loop.py` y `tests/test_cathedral_vectors.py`.

**Implicación:** no es seguro copiar carpetas completas ni reemplazar archivos por nombre. La integración debe ser selectiva y basada en diffs revisados línea por línea.

### 2. Archivos que existen en el principal pero no en el clon

- `elite/FEX/GOVERNANCE/economic_cycle.py`
- `elite/REASON/dynamic_constraints.py`
- `elite/bin/impact_cycle.py`
- `tests/test_dynamic_constraints.py`
- `tests/test_economic_cycle.py`

**Implicación:** estos componentes y sus pruebas podrían perderse si se reemplazaran directorios completos del principal con el contenido del clon. Deben conservarse y evaluar su compatibilidad explícitamente.

### 3. Archivos que existen solo en el clon

La lista incluye la documentación y pruebas de revisión, además de componentes nuevos:

- `elite/DSX/DEFENSE/guards.py`
- `elite/FEX/GOVERNANCE/sustainability.py`
- `elite/MSX/` (procedencia)
- `elite/REASON/cognitive_state.py`
- `elite/REASON/core_contract.py`
- `elite/REASON/fex_feedback_adapter.py`
- `elite/REASON/master_cycle.py`
- `elite/REASON/report_composition.py`
- `tests/test_acceptance_contract.py`
- `tests/test_order_safety.py`
- `tests/test_panic_integration.py`
- `tests/test_sustainability_governance.py`
- `tests/test_vector_contracts.py`
- `scripts/verify_isolated_safety.sh`
- Documentación de auditoría, evaluación y aceptación en la raíz y `docs/`.

**Implicación:** son candidatos a revisión, no cambios autorizados para integración automática. Debe revisarse su import graph y compatibilidad con los componentes exclusivos del principal.

## Riesgos y decisión

1. **Bloqueo de integración:** existen cambios superpuestos en rutas críticas y módulos presentes solo en el principal.
2. **Sin pérdida accidental:** preservar los archivos exclusivos del principal; no usar copias recursivas ni reemplazos masivos.
3. **Siguiente paso recomendado:** preparar una tabla por archivo con (a) cambio del clon, (b) cambio preexistente del principal, (c) conflicto funcional, (d) pruebas afectadas y (e) decisión mantener/combinar/descartar.
4. Ejecutar las pruebas relevantes del principal y del clon por separado después de cualquier integración autorizada.
5. La aprobación técnica no elimina los bloqueos de producción registrados en `MATRIZ_ACEPTACION_PERGAMINO.md`.

## Límites de esta revisión

Esta comparación es un inventario de rutas y contenido, no una revisión semántica línea por línea de las 16 diferencias. No se concluye que el clon sea superior ni que todos sus componentes estén listos para integrar. No se modificó el repositorio principal.
