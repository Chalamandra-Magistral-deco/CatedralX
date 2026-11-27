# CatedralX

**CatedralX es un motor de razonamiento y análisis financiero experimental del ecosistema Chalamandra Magistral.** Su función es transformar observaciones de mercado y contexto computable en resultados estructurados, reproducibles y verificables. No es un chatbot ni un ejecutor autónomo de operaciones.

## ¿Qué hace?

En su implementación financiera actual, CatedralX:

- recibe series cronológicas de precios observados y valida su integridad;
- calcula métricas de rendimiento, volatilidad, drawdown, medias móviles e impulso;
- clasifica escenarios mediante reglas deterministas y devuelve etiquetas analíticas `buy`, `sell` o `hold`;
- aplica condiciones de protección que pueden bloquear una señal direccional;
- conserva estado y registros de evaluación fuera del checkout del repositorio;
- permite evaluar predicciones posteriormente mediante observaciones reales y métricas estadísticas.

Los subsistemas de análisis complementarios —incluidos Hurst, geometría, energía libre y giro— forman parte del contexto analítico del proyecto. Su presencia no implica que cada uno determine por sí solo la clasificación financiera final.

## Qué no hace

CatedralX no crea precios sintéticos para completar datos faltantes, no convierte una puntuación heurística en una probabilidad de acierto y no crea ni ejecuta órdenes.

Las etiquetas `buy`, `sell` y `hold` son resultados de análisis, no recomendaciones de inversión. La implementación actual no está validada para trading real ni debe conectarse a una cuenta como sistema de producción.

## Arquitectura del repositorio

El código ejecutable y los componentes del sistema se mantienen separados de la documentación:

- `elite/`: subsistemas y lógica principal.
- `elite/contracts/`: contratos y esquemas consumidos por el sistema.
- `BIN/`: punto de entrada de línea de comandos.
- `tests/`: pruebas automatizadas.
- `.github/workflows/`: automatización de integración continua.
- `docs/`: documentación técnica, arquitectura, decisiones y guías.
- `Dockerfile`: definición de la imagen CLI.

Los archivos de configuración y dependencias se encuentran en la raíz del repositorio.

## Requisitos

- Python 3.12 o superior.
- Dependencias de runtime declaradas en `requirements.txt`.
- Versiones exactas de dependencias registradas en los archivos lock del proyecto.

## Inicio rápido

Desde la raíz del repositorio:

```bash
python -m pip install -r requirements-lock.txt
./BIN/catedral status
```

Para ejecutar las pruebas:

```bash
python -m pip install -e ".[test]"
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q
```

La imagen Docker está diseñada para ejecutar la CLI en modo puntual; no representa un servicio HTTP persistente.

## Datos y persistencia

El estado operativo y los registros de retroalimentación se almacenan por defecto bajo:

```text
~/.local/state/chalamandra/catedralx/
```

Las rutas pueden configurarse mediante variables de entorno específicas. Los datos de estado no deben guardarse dentro del checkout del repositorio.

## Estado y límites de validación

El proyecto se encuentra en desarrollo. La reproducibilidad de las reglas y la existencia de pruebas automatizadas no equivalen a demostrar rentabilidad ni aptitud para operar capital real.

Antes de cualquier uso operativo se requiere, como mínimo, backtesting con datos históricos y costes realistas, validación fuera de muestra, comparación con benchmarks, análisis de estabilidad, límites de riesgo y auditoría independiente.

Consulta `docs/` para la documentación técnica disponible y vigente.
