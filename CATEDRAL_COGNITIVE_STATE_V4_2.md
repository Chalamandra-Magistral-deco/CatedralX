# CatedralX — contrato cognitivo v4.2 (implementación aislada)

**Ubicación:** CatedralX-verify
**Vector principal:** SCX / REASON
**Estado:** implementado parcialmente y probado; análisis solamente.
**No representa** una certificación de calibración ni aprendizaje autónomo.

## Capacidades añadidas

- elite/REASON/cognitive_state.py: funciones puras para coherencia direccional, contraevidencia, incertidumbre, diagnóstico metacognitivo, contexto de Markov, memoria de decisiones y provenance SHA-256.
- elite/REASON/orchestrator.py: incorpora el informe cognitivo al paquete del ciclo; una contradicción que excede los límites produce HOLD y revisión, nunca una orden.
- tests/test_cognitive_state.py: pruebas para datos ausentes, contradicciones, memoria, contexto y trazabilidad.

## Las seis preguntas del Pergamino

| Pregunta | Campo |
|---|---|
| ¿Qué creo que está pasando? | cognicion.contexto |
| ¿Qué tan seguro estoy? | cognicion.metacognicion; calcula brecha solo cuando hay historial etiquetado disponible |
| ¿Por qué decidí esto? | cognicion.provenance y las señales explícitas usadas |
| ¿Qué evidencia contradice mi decisión? | cognicion.contraevidencia y cognicion.coherencia |
| ¿Qué aprendí del ciclo anterior? | cognicion.memoria; resume decisiones, no ajusta parámetros |
| ¿Cómo cambió mi estado interno? | cognicion.contexto.historial_fases y memoria acotada en el proceso |

## Semántica y límites

- Las señales solo participan en coherencia si tienen dirección explícita y confianza numérica válida.
- signal_strength y la confianza heurística del giroscopio no son probabilidades calibradas.
- La disonancia se define como (1 - coherencia) / 2 para que oposición perfecta (coherencia = -1) produzca disonancia 1. La fórmula 1 - abs(coherencia) no detectaría la oposición perfecta y por eso no se usa.
- Las señales neutrales se registran, pero no se cuentan como evidencia direccional de acuerdo ni contradicción.
- El historial de régimen/decisiones vive en memoria del proceso, está acotado y se pierde al reiniciar. No hay aprendizaje de parámetros ni consolidación offline implementados.
- Brier/ECE, calibración Platt/isotónica, separación epistémica/aleatoria estimada desde modelos, causalidad, utilidad esperada y tamaño de posición validado quedan no disponibles hasta contar con datos y validación adecuados.
- No se inventan métricas ni resultados cuando faltan datos: los campos permanecen null y el estado indica que la evidencia es insuficiente.
- trading_enabled=false, orders_created=false y orders_executed=false se mantienen como límites duros.

## Verificación

- PYTHONPATH=elite:. python -m pytest -q — 130 pruebas aprobadas.
- git diff --check — correcto.
- python -m compileall para los módulos cognitivos y orquestador — correcto.
- scripts/verify_isolated_safety.sh — pruebas, análisis sintético de humo y bloqueo de emergencia aprobados.

Todos los cambios pertenecen a CatedralX-verify. No se creó commit, no se hizo push ni despliegue. El repositorio original no se modificó en esta ejecución.