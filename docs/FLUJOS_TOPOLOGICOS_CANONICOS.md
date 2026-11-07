# Definición Canónica de los Tres Flujos (v4.2)

Este documento formaliza la semántica de los flujos de información en CatedralX, resolviendo cualquier ambigüedad sobre "inversiones matemáticas". Los flujos son **direcciones topológicas de despliegue**.

## 1. Flujo Normal (Entrada)
- **Ruta**: Usuario (fuera) → API (VM) → Agente (VM) → CatedralX (VM).
- **Propósito**: Ingesta de solicitudes, validación de contratos y procesamiento causal hacia el motor.
- **Estado final**: `CathedralState` con decisión candidata (ej. `ANALYSIS_COMPLETE hold`).

## 2. Flujo Inverso (Retorno / Publicación)
- **Ruta**: CatedralX (VM) → Agente (VM) → API (VM) → Usuario (fuera).
- **Propósito**: Entrega del resultado aceptado, notificaciones vía webhook y retroalimentación al origen de la petición.
- **Nota**: No es una inversión matemática de la función; es el camino de retorno simétrico de la topología de red.

## 3. Flujo Invertido (Iniciativa Proactiva)
- **Ruta**: CatedralX (VM) origina → Agentes (VM) → API (VM) → Productos (fuera).
- **Propósito**: El motor inicia un ciclo de trabajo basado en condiciones internas, timers o detección de oportunidades, sin una petición externa previa.
- **Implementación**: `elite/bin/impact_cycle.py`, `dispatch_agents.py`.

## 4. Aritmética y Defensa Asociada
- Todas las evaluaciones de política usan **basis points enteros** (`[0, 10000]`).
- El sistema es **fail-closed**: cualquier valor no entero o fuera de rango dispara `DATOS_INVALIDOS`.
- El concepto de "invasiones" se materializa operacionalmente como violaciones de invariantes detectadas por **Defensa Lateral** (`guardian_ram`) y el mecanismo de **PATH_PANIC**.
