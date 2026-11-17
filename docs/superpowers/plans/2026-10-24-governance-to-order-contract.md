# Governance-to-Order Contract Implementation Plan

> Execute inline with TDD. No commit, push, merge, deploy, real market order, or modification of the original repository.

**Goal:** Ensure AEX cannot persist a pending order unless a valid DSX decision explicitly permits it and the FEX sustainability evaluation is complete and permits growth.

**Architecture:** Reuse the existing `FEX/GOVERNANCE/sustainability.py`, `DSX/DEFENSE/guards.py`, `MSX/provenance.py`, and `AEX/DECISION/ordenes.py`. DSX enforces, FEX evaluates, SCX reports cognitive evidence, MSX only traces. Do not add parallel vector modules.

**Tech Stack:** Python 3, pytest, existing repository venv.

**Spec:** User's Pergamino consolidation protocol (current conversation), `AUDITORIA_CONSOLIDACION_PERGAMINO.md`, and `CATEDRAL_COGNITIVE_STATE_V4_2.md`.

## Entorno

La ruta local del plan se ha normalizado como `<CATEDRALX_VERIFY_ROOT>`; la VM asociada fue retirada. Este plan no presupone que ese checkout o entorno sigan disponibles.

## Global Constraints

- Work only in `<CATEDRALX_VERIFY_ROOT>`.
- No live exchange client, real order execution, publish, commit, or push.
- Missing or invalid mandatory governance evidence must fail closed.
- DSX enforces; SCX calculates cognitive evidence; FEX evaluates sustainability; MSX observes/traces; AEX persists only a pending local order.
- Preserve existing public APIs unless an intentional safety contract requires a new required argument.

## Review Focus

- Missing governance metrics or a missing sustainability report must block order persistence.
- A signed approval token must not bypass DSX or sustainability gates.
- `NaN`, infinity, booleans in numeric fields, and threshold boundaries must not be treated as valid evidence.
- Panic marker or unavailable panic path must continue to block.
- Valid analysis must remain non-executing and no live exchange path may be introduced.

## Tasks

### Task 1: Prove DSX gate behavior
- Add tests for dissonance above 0.40, counterevidence above threshold, panic, and missing contraevidence.
- Run tests and observe expected failures before changing the guard.
- Make the minimal in-place change to `elite/DSX/DEFENSE/guards.py` only if needed.
- Run targeted tests.

### Task 2: Bind AEX order persistence to DSX + FEX governance
- Add failing tests proving a signed token alone, missing governance, incomplete metrics, failed sustainability report, or blocked DSX gate cannot create `orden.json`.
- Add a required, validated governance authorization argument to `generar_orden`; require DSX `allowed=True`, `blocked=False`, `enforcement_vector='DSX'`, complete finite sustainability metrics, `crecimiento_permitido=True`, empty failures, and `ejecucion_financiera_autorizada=False`.
- Update only synthetic tests to pass a valid gate/report. Never invoke a broker.
- Run targeted tests and verify output paths remain under `tmp_path`.

### Task 3: Full verification and audit
- Run the full pytest suite, compileall, `git diff --check`, and `scripts/verify_isolated_safety.sh`.
- Inspect final diff and check original repository status without changing it.
- Report limitations and exact evidence; do not claim Auditor signature or integration approval.
