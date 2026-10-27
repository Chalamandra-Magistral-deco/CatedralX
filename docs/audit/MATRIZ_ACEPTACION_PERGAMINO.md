# Matriz de aceptación del Pergamino — CatedralX

**Ámbito:** clon de revisión `CatedralX-verify`  
**Fecha:** 2026-10-24  
**Estado global:** revisión parcial; **NO APTO PARA PRODUCCIÓN**.  
**Regla:** “Verificado” significa que existe evidencia de código/pruebas en este clon; no significa auditoría independiente ni seguridad de producción.

| Frontera / requisito | Estado | Evidencia comprobable | Brecha / siguiente acción |
|---|---|---|---|
| SCX calcula coherencia, disonancia y contraevidencia; no ejecuta ni bloquea por sí mismo | **Verificado en clon** | `elite/REASON/cognitive_state.py`; `tests/test_cognitive_state.py`; `tests/test_vector_contracts.py` | Mantener enforcement fuera de SCX. |
| SCX → DSX: DSX consume diagnósticos y aplica enforcement | **Verificado en clon** | `elite/DSX/DEFENSE/guards.py`; pruebas de umbral, evidencia no finita y contraevidencia en `tests/test_vector_contracts.py` | Revisar la matriz completa de límites frente al Pergamino durante auditoría independiente. |
| Composición SCX + memoria FEX + procedencia MSX sin mezclar propiedad de cálculos | **Parcial** | `elite/REASON/report_composition.py`; `tests/test_vector_contracts.py` | La integración de memoria y procedencia existe; la calibración histórica real y el aprendizaje validado con resultados observados no quedan demostrados por estas pruebas. |
| FEX: gobernanza de sostenibilidad y evidencia | **Verificado en clon para reglas sintéticas** | `elite/FEX/GOVERNANCE/sustainability.py`; `tests/test_sustainability_governance.py`; `tests/test_order_safety.py` | Confirmar métricas y origen de datos operativos reales antes de cualquier uso fuera de pruebas. |
| MSX: procedencia y agregación de ciclo | **Parcial** | `MSX/provenance.py`; `tests/test_vector_contracts.py` verifica hash, padre, agregación y rechazo de duplicados | Validar en auditoría el contrato completo exigido por el Pergamino —vector, módulo, versión, timestamp, input_hash, output, confidence y parent— en todos los productores; telemetría de salud completa también queda pendiente. |
| DSX → AEX: autorización firmada, vinculada a intención, TTL y fail-closed | **Verificado en clon con identidad sintética** | `elite/DSX/DEFENSE/guards.py`; `elite/AEX/DECISION/ordenes.py`; `tests/test_order_safety.py` | El verificador de identidad real no está configurado; las pruebas usan un proveedor de identidad simulado. No habilitar producción. |
| AEX: solo orden pendiente local, sin ejecución real | **Verificado como límite de diseño del clon** | `elite/AEX/DECISION/ordenes.py`; pruebas de seguridad de órdenes | No hay autorización para broker ni órdenes reales; conservar trading deshabilitado. |
| Firma/aprobación: falsificación, permiso, precio/acción y expiración | **Verificado en pruebas sintéticas** | `tests/test_order_safety.py` | La confianza real depende de IdP externo y gestión segura de claves fuera de estas pruebas. |
| Keyrings versionados y rotación | **Parcial** | Configuración de keyring en `elite/DSX/DEFENSE/guards.py` y `elite/AEX/DECISION/ordenes.py` | Existe compatibilidad legacy; falta configurar y ensayar una rotación real, revocación y operación segura de secretos. |
| Persistencia y concurrencia multiproceso | **Pendiente** | No se considera demostrada por la suite unitaria actual | Añadir pruebas de durabilidad, atomicidad, carreras y recuperación ante caída antes de cualquier aprobación operativa. |
| Schema v4.2 y compatibilidad hacia delante | **Parcial** | `SCHEMA_VERSION = "4.2-cognitive-draft"` en `elite/REASON/cognitive_state.py` | La etiqueta indica borrador; demostrar contratos de compatibilidad y migración sin alterar datos existentes. |
| Rendimiento, determinismo y resiliencia de recursos | **Parcial** | Hay pruebas de contratos y recursos en `tests/test_resource_monitor.py` y `tests/test_snapshot_freshness.py` | Falta evidencia de pruebas de estrés/repetibilidad y tolerancia a fallos bajo carga representativa. |
| Evidencia de ventaja financiera estable | **Pendiente / no demostrada** | `RESEARCH_EVALUATION_2026-10-24.md` | Resultados de investigación no demuestran edge neto estable; costes, spread y slippage no están incorporados plenamente. No usar como fundamento de ejecución real. |
| Clon frente al repositorio principal | **Pendiente** | Esta matriz solo evalúa el clon `CatedralX-verify` | Comparar diferencias e inventario antes de proponer integración. No copiar, fusionar ni desplegar automáticamente. |
| Revisión y firma independiente del Auditor | **Pendiente** | No se afirma una firma independiente | Solicitar revisión del expediente y registrar dictamen verificable antes de integrar. |
| Liberación a producción | **Bloqueado** | Brechas abiertas de identidad, claves, persistencia/concurrencia, revisión independiente y evidencia financiera | Mantener bloqueada. No desplegar, no habilitar trading y no emitir órdenes reales. |

## Verificaciones del clon registradas

La verificación ejecutada tras incorporar esta matriz reportó **210 pruebas aprobadas**, ejecución exitosa de `scripts/verify_isolated_safety.sh`, `compileall` y `git diff --check`. Esta matriz es documentación adicional; volver a ejecutar pruebas y controles de diferencias tras incorporarla.

## Criterio de salida

Solo reconsiderar la integración cuando: (1) las brechas pendientes tengan pruebas reproducibles; (2) el proveedor de identidad y la gestión de claves estén configurados y auditados; (3) se compare explícitamente el clon con el repositorio principal; y (4) el Auditor independiente emita su dictamen. La autorización de integrar y cualquier liberación siguen siendo decisiones separadas.
