# CatedralX — evaluación histórica de señales (2026-10-24 UTC)

## Nota de entorno

La ubicación del artefacto se ha normalizado: el directorio original pertenecía a una VM retirada y no debe interpretarse como almacenamiento disponible actualmente.

## Decisión operativa

**Mantener CatedralX en análisis únicamente. No habilitar trading ni conectar un bróker.** La muestra no muestra una ventaja direccional estable, y los resultados son brutos, sin costes.

## Datos y método

- Fuente: endpoint público de velas spot de Binance; símbolo `BTCUSDT`.
- Intervalo: velas de un minuto, solo velas cerradas y observaciones consecutivas. No se interpolaron huecos.
- Ventana: `2026-09-24T02:05:00Z` a `2026-10-24T02:03:59.999Z`.
- Datos: 43,199 velas cerradas.
- En cada cierre, el motor clasifica usando las últimas 60 observaciones; el resultado se compara con el retorno observado después de 1, 5, 15, 30 y 60 minutos.
- Etiqueta futura: `buy` si el retorno es al menos +0.05%, `sell` si es como máximo -0.05%, `hold` si queda entre ambos. Es un umbral de evaluación, no una instrucción de operación.
- Comparador de clasificación: predecir `hold` para todos los casos.
- Las mitades cronológicas son diagnósticos de estabilidad; no se ajustaron parámetros ni se entrenó un modelo.

## Resultados del periodo completo

| Horizonte | Muestras | Exactitud motor | Exactitud siempre HOLD | Cobertura direccional | Acierto de signo en señales direccionales | Retorno direccional alineado medio antes de costes |
|---|---:|---:|---:|---:|---:|---:|
| 1 minuto | 43,139 | 65.45% | 82.89% | 25.14% | 48.37% | +0.00085% |
| 5 minutos | 43,135 | 47.17% | 54.22% | 25.14% | 46.74% | -0.00149% |
| 15 minutos | 43,125 | 35.20% | 36.29% | 25.13% | 46.66% | -0.00333% |
| 30 minutos | 43,110 | 28.79% | 27.10% | 25.14% | 46.74% | -0.00547% |
| 60 minutos | 43,080 | 23.59% | 18.25% | 25.14% | 47.46% | -0.00821% |

La exactitud por sí sola puede ser engañosa ante distintas proporciones de `buy`/`sell`/`hold`. Aunque la exactitud supera al comparador siempre-HOLD a 30 y 60 minutos, el acierto de signo direccional continúa por debajo del 50% y el retorno alineado medio es negativo. En el horizonte de un minuto el retorno alineado medio es apenas positivo, pero el acierto de signo también está por debajo del 50% y el resultado no incluye costes.

## Límites

Esta es una evaluación de etiquetas/señales, **no** una simulación completa de estrategia ni un resultado de cartera. No incluye tarifas, spread, deslizamiento, financiación, posiciones, límites de exposición ni reglas de entrada/salida realistas. Por tanto, no prueba rentabilidad futura ni ventaja estadística.

## Artefacto de datos

Reporte JSON completo guardado fuera del checkout:

`<LEGACY_STATE_DIR>/chalamandra/catedralx/reports/btcusdt_1m_30d_20261024T020416Z.json`

El reporte de siete días también está guardado en el mismo directorio. El evaluador se encuentra en `scripts/backtest_public_candles.py` y permite repetir la comparación con `--compare-horizons`.

## Próximo paso recomendado

No retocar umbrales usando este mismo periodo. Primero verificar los resultados en un periodo cronológico distinto y, si se propone una estrategia, definir de antemano reglas de entrada/salida, tamaño, límites de riesgo, costes y comparadores; después hacer un backtest walk-forward con esos parámetros fijados. Hasta entonces, mantener `trading_enabled=false` y `orders_executed=false`.
