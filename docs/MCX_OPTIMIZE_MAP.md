# MCX vs OPTIMIZE - Clarificación canónica

## Fuentes canónicas separadas - NO duplicados

**elite/OPTIMIZE/optimize.py** (top-level)
- v4.2 sensibilidad hormonal
- palanca_beta(dopamina, cortisol, serotonina, volatilidad, gap)
- estado_homeostatico -> beta_precision, modo AGRESIVO/CONSERVADOR/EQUILIBRADO
- Uso: transductor endocrino, sensibilidad hormonal

**elite/MCX/OPTIMIZE/**
- 10 módulos: affective, entropia, ganancias, homeostasis, kelly_vince, mental, optimize, poder_real, resico, sentiment_engine
- RL primitives: softmax, q_learning_actualizar, bellman
- Uso: homeostasis + optimización + RL

**Relación:**
OPTIMIZE top-level = capa hormonal (hormonas -> beta)
MCX/OPTIMIZE = capa RL + homeostasis (beta -> acciones)

Mantener ambos, no consolidar.

## Verificación
- from OPTIMIZE.optimize import palanca_beta, estado_homeostatico
- from MCX.OPTIMIZE.entropia import * etc
