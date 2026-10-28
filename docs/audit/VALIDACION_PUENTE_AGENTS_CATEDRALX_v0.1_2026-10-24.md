# Validación aislada del puente agents → CatedralX
**Fecha:** 2026-10-24  
**Versión:** 0.1  
**Entorno:** VM chalamandra-vm; sin llamadas a proveedores de IA ni API de mercado.  
**Repositorios:** checkout local agents y worktree CatedralX-verify (HEAD separado ec92163, con modificaciones preexistentes).

## Resultado

**Estado: PASÓ en pruebas locales aisladas; runtime productivo no certificado.**

### 1. Suite offline de contrato y registro

Comando usado desde ~/workspace/repos/agents:

    PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python -m pytest -q -p no:cacheprovider tests/test_catedralx_tool.py tests/test_master.py tests/test_tool_registry.py

Resultado observado: **21 passed in 3.58s**, código de salida 0.

Los tests incluyen registro de catedralx_reasoning, validación de precios, mínimo de 30 observaciones, rechazo de precios inválidos, protección de la ruta de estado, origen diario simulado, señal contradictoria y banderas de no ejecución de órdenes.

### 2. Prueba de humo con el motor real

Se invocó Master.execute_agent_tool_call("analyst", ...) y el handler catedralx_reasoning apuntó explícitamente a CatedralX-verify, no al checkout principal. Entrada: una serie local sintética de 60 precios únicamente para probar el contrato; no representa precios de mercado ni señal financiera.

La variable CATEDRALX_STATE_PATH apuntó a un directorio temporal bajo /tmp; el directorio se eliminó al terminar. Se estableció PYTHONDONTWRITEBYTECODE=1. No se llamó a Frankfurter, brokers ni modelos de IA.

Salida resumida observada:

    status=ok
    engine=CatedralX
    asset=TEST/EUR
    data_source=provided
    signal_consistent=true
    trading_eligible=false
    orders_created=false
    orders_executed=false
    error=null

### 3. Protección de cambios existentes

El git status --short antes y después fue idéntico en los dos checkouts:

- agents: permanecieron modificados core/decomposer.py, core/executor.py, tests/test_decomposer.py y tests/test_executor.py.
- CatedralX-verify: permanecieron las modificaciones y archivos no rastreados preexistentes del worktree. No se limpiaron ni sobrescribieron.

No se hizo commit, push, merge, despliegue ni cambio de configuración de producción.

## Interpretación y pendientes

- **VERIFICADO en entorno aislado:** la herramienta está registrada, pasa 21 tests de contrato/registro y el handler puede cargar el motor real del worktree de verificación con una entrada explícita de prueba.
- **NO VERIFICADO:** configuración real del proceso/servicio que consumiría el puente, programación de ejecución, integración continua, datos frescos, monitorización y despliegue.
- **BLOQUEADO para trading real:** trading_eligible=false, orders_created=false y orders_executed=false en la prueba; CatedralX se mantiene como motor experimental de análisis, no como ejecutor de órdenes.
- Esta prueba no certifica la copia principal de CatedralX, ni valida ventaja predictiva o rentabilidad financiera.
