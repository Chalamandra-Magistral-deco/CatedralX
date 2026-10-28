#!/usr/bin/env python3
"""Submit an explicitly authorized task from CatedralX to the local Agents API.

This command is deliberately opt-in. The canonical motor never dispatches tasks
implicitly, avoiding recursion when Agents invokes CatedralX as a tool.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import ipaddress
import json
import os
import re
import socket
import sys
import time
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _make_service_jwt(secret: str, now: int | None = None) -> str:
    if not secret:
        raise ValueError("CHALAMANDRA_JWT_SECRET no está configurado")
    issued = int(time.time()) if now is None else int(now)
    header = {"alg": "HS256", "typ": "JWT"}
    claims = {
        "sub": "catedralx-service",
        "scope": "orchestration:run",
        "iat": issued,
        "exp": issued + 60,
    }
    signing_input = (
        _b64url(json.dumps(header, separators=(",", ":"), sort_keys=True).encode())
        + "."
        + _b64url(json.dumps(claims, separators=(",", ":"), sort_keys=True).encode())
    )
    signature = hmac.new(secret.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
    return signing_input + "." + _b64url(signature)


def _make_traceparent(value: str | None = None) -> str:
    """Return a strict W3C traceparent; generate a fresh root when none is supplied."""
    candidate = value or f"00-{uuid.uuid4().hex}-{uuid.uuid4().hex[:16]}-01"
    match = re.fullmatch(r"([0-9a-f]{2})-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})", candidate)
    if not match:
        raise ValueError("traceparent no cumple el formato W3C Trace Context")
    version, trace_id, parent_id, _flags = match.groups()
    if version == "ff" or trace_id == "0" * 32 or parent_id == "0" * 16:
        raise ValueError("traceparent contiene identificadores W3C inválidos")
    return candidate


def _validate_api_url(api_url: str) -> str:
    parsed = urlsplit(api_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("CHALAMANDRA_API_URL debe ser una URL HTTP(S) válida")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("CHALAMANDRA_API_URL no admite credenciales, query ni fragment")
    if parsed.scheme == "http":
        try:
            address = ipaddress.ip_address(parsed.hostname)
            loopback = address.is_loopback
        except ValueError:
            loopback = parsed.hostname.lower() == "localhost"
            if not loopback:
                try:
                    resolved = socket.getaddrinfo(parsed.hostname, parsed.port or 80, type=socket.SOCK_STREAM)
                    loopback = bool(resolved) and all(
                        ipaddress.ip_address(item[4][0]).is_loopback for item in resolved
                    )
                except (OSError, ValueError):
                    loopback = False
        if not loopback:
            raise ValueError("HTTP sin TLS solo se permite en loopback")
    return api_url.rstrip("/")


# Keep the CLI as a thin adapter; cycle validation belongs to CatedralX's canonical ledger.
ELITE_DIR = Path(__file__).resolve().parents[1]
if str(ELITE_DIR) not in sys.path:
    sys.path.insert(0, str(ELITE_DIR))
from FEX.GOVERNANCE.economic_cycle import cargar_propuesta_autorizada


def load_authorized_proposal(ledger_path: Path, cycle_id: str) -> dict:
    """Compatibility wrapper around CatedralX's canonical proposal validator."""
    try:
        return cargar_propuesta_autorizada(ledger_path, cycle_id)
    except OSError as exc:
        raise ValueError(f"No se pudo leer el ledger económico: {exc}") from exc


def dispatch_task(
    objective: str,
    payload: dict,
    api_url: str,
    secret: str,
    timeout: float = 5.0,
    idempotency_key: str | None = None,
    traceparent: str | None = None,
) -> dict:
    if not isinstance(objective, str) or not objective.strip():
        raise ValueError("El objetivo debe ser texto no vacío")
    if not isinstance(payload, dict):
        raise TypeError("El payload debe ser un objeto JSON")
    if idempotency_key is not None and (
        not idempotency_key.strip()
        or len(idempotency_key) < 8
        or len(idempotency_key) > 128
        or "\r" in idempotency_key
        or "\n" in idempotency_key
    ):
        raise ValueError("Idempotency-Key debe tener entre 8 y 128 caracteres válidos")
    base_url = _validate_api_url(api_url)
    parent = _make_traceparent(traceparent)
    token = _make_service_jwt(secret)
    body = {
        "objective": objective.strip(),
        "payload": payload,
        "permissions": {"allowed_tools": []},
        "success_criteria": [
            "La ejecución termina y produce un candidato trazable; la aceptación independiente es obligatoria."
        ],
    }
    request = Request(
        base_url + "/internal/v1/orchestration/runs",
        data=json.dumps(body, ensure_ascii=False, allow_nan=False).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "traceparent": parent,
            **({"Idempotency-Key": idempotency_key} if idempotency_key else {}),
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            response_body = response.read().decode("utf-8")
            result = json.loads(response_body) if response_body else {}
            if response.status != 202:
                raise RuntimeError(f"Agents API respondió HTTP {response.status}")
            return result
    except HTTPError as exc:
        detail = exc.read(1000).decode("utf-8", "replace")
        raise RuntimeError(f"Agents API respondió HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"No se pudo conectar con Agents API: {exc.reason}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--cycle-id", help="Despachar una propuesta económica autorizada de CatedralX")
    mode.add_argument("--objective", help="Objetivo de tarea explícita")
    parser.add_argument("--payload-file", type=Path, help="JSON de contexto para --objective")
    parser.add_argument(
        "--ledger-path", type=Path,
        help="Ledger económico (solo para --cycle-id; por defecto usa CATEDRALX_IMPACT_LEDGER_PATH)",
    )
    parser.add_argument("--idempotency-key", help="Clave para impedir la duplicación de tareas")
    parser.add_argument("--traceparent", help="W3C traceparent entrante; se genera uno si se omite")
    parser.add_argument(
        "--api-url",
        default=os.getenv("CHALAMANDRA_API_URL", "http://127.0.0.1:8766"),
        help="API local; por defecto http://127.0.0.1:8766",
    )
    parser.add_argument("--timeout", type=float, default=5.0)
    args = parser.parse_args()

    if not 0 < args.timeout <= 30:
        parser.error("--timeout debe estar entre 0 y 30 segundos")
    if args.objective and not args.payload_file:
        parser.error("--objective requiere --payload-file")
    if args.cycle_id and args.payload_file:
        parser.error("--payload-file no se combina con --cycle-id")

    try:
        idempotency_key = args.idempotency_key
        if args.cycle_id:
            configured_ledger = os.getenv(
                "CATEDRALX_IMPACT_LEDGER_PATH",
                str(Path.home() / ".local/state/chalamandra/catedralx/impact_cycle.jsonl"),
            )
            ledger_path = args.ledger_path or Path(configured_ledger).expanduser()
            payload = load_authorized_proposal(ledger_path, args.cycle_id)
            objective = "catedralx_economic_proposal_review"
            if idempotency_key is None:
                idempotency_key = "catedralx-economic-cycle:" + args.cycle_id
        else:
            if not args.payload_file or not args.objective:
                parser.error("Se requiere --objective y --payload-file, o --cycle-id")
            payload = json.loads(args.payload_file.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("El archivo payload debe contener un objeto JSON")
            objective = args.objective
        response = dispatch_task(
            objective,
            payload,
            args.api_url,
            os.getenv("CHALAMANDRA_JWT_SECRET", ""),
            timeout=args.timeout,
            idempotency_key=idempotency_key,
            traceparent=args.traceparent,
        )
    except (OSError, json.JSONDecodeError, ValueError, TypeError, RuntimeError) as exc:
        print(json.dumps({"status": "error", "reason": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1

    print(json.dumps(response, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
