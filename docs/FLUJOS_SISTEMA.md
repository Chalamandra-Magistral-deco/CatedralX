# FLUJOS_SISTEMA - CatedralX v1.0 canónico

## ENTRY CANÓNICO
BIN/catedral -> orquesta status/feed-once/motor/ciclo/impact-cycle/user-feedback/dispatch-agents/test
docs/legacy/motor.py -> wrapper DEPRECATED histórico; no es BIN/motor.py

## FUENTES DE ESTADO SEPARADAS - NO DUPLICADAS
- RSX /dev/shm/cathedral_snapshot.json -> CATEDRALX_SNAPSHOT_PATH -> PERCEIVE.data_feeder.snapshot_path() CANONICO
  59 velas Binance BTCUSDT 1m, price, observed_at, healthy max 120s
- STATE ~/.local/state/chalamandra/catedralx/hormonas.json -> CATEDRALX_STATE_PATH -> REASON.state_paths.canonical_state_path() CANONICO
  hormonas, cycle_id, market_phase, geometry_regime

## PERCEIVE
data_feeder.snapshot_path() CANONICO RSX
api_pulse.check_snapshot() healthy true/false
stream_altar fetch Binance

## REASON
orchestrator.execute_cycle(sensory) -> CathedralState
state_paths.canonical_state_path() STATE separado
razon.main() -> path=snapshot_path() + from_snapshot + execute_cycle -> ANALYSIS_COMPLETE hold

## NEXUS
elite/bin/nexus.py status() ahora muestra rsx_path + state_path + feed.healthy + state_available

## LOOPBACK
inyector-vitral no localizado en el árbol de este checkout; endpoints/puerto 127.0.0.1:5050 quedan sin verificar aquí.

## SEGURIDAD
trading_enabled false, orders_created false, orders_executed false en todos los paths
AEX ejecutor preparar_intencion -> BLOCKED_REVIEW_ONLY
DSX guards HMAC keyring versionado + PATH_PANIC ~/LAB/03-OUTPUT/.panic
FEX prediction/outcome ledger ~/.local/state/chalamandra/catedralx/feedback.jsonl
User feedback ledger ~/.local/state/chalamandra/catedralx/user_feedback.jsonl

## MAPA_MAESTRO
MAPA_MAESTRO_CANONICO.md 34K v0.8 = v0.7 (Vercel env + AI Studio) + v0.5 (Supabase contrast)
docs/archive/ 6 versiones v0.2-v0.7 thrashing archivado

## TESTS
./BIN/catedral test -> 337 passed en la suite local del checkout (2026-10-28; sin despliegue).
./BIN/catedral feed-once -> FEED_UPDATED 59 velas
./BIN/catedral status -> healthy true/false + rsx_path + state_path
./BIN/catedral motor -> ANALYSIS_COMPLETE hold


## MECÁNICA Y FEEDBACK DE USUARIO

Ver [docs/ARQUITECTURA_MECANICA_RETROALIMENTACION.md](ARQUITECTURA_MECANICA_RETROALIMENTACION.md) para responsabilidades, candidatos de limpieza pendientes de confirmación y el ledger de feedback directo.
