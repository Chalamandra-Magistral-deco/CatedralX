# inyector-vitral - Loopback status endpoint

**Ubicación:** elite/bin/inyector-vitral
**Puerto:** 127.0.0.1:5050
**Endpoints:** /status /health
**Seguridad:** loopback-only, read-only, usa nexus.status()
**Uso:** python3 elite/bin/inyector-vitral & curl http://127.0.0.1:5050/status
**Valor:** HTTP read-only para monitoring sin exponer snapshot

Valioso no documentado - mantener como herramienta opcional.
