"""Append-only ResultStore for CatedralX (Fase 0)."""
import json
import os
from pathlib import Path
from typing import Any

def default_result_store_path() -> Path:
    configured = os.environ.get("CATEDRALX_RESULT_STORE_PATH")
    candidate = (
        Path(configured).expanduser()
        if configured
        else (
            Path.home()
            / ".local"
            / "state"
            / "chalamandra"
            / "catedralx"
            / "results.jsonl"
        )
    )
    resolved = candidate.resolve()
    repo_root = Path(__file__).resolve().parents[2]
    if resolved == repo_root or repo_root in resolved.parents:
        raise ValueError("CATEDRALX_RESULT_STORE_PATH debe estar fuera del repositorio")
    return resolved

def append_result(record: dict[str, Any], path: str | Path | None = None) -> str:
    """Append a DecisionResult to the store. Returns the result_id."""
    target = Path(path) if path else default_result_store_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    
    result_id = record.get("result_id")
    if not isinstance(result_id, str) or not result_id.strip():
        raise ValueError("El record debe tener un 'result_id' válido")
        
    with target.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False, allow_nan=False, sort_keys=True) + "\n")
    return result_id

def get_result(result_id: str, path: str | Path | None = None) -> dict[str, Any] | None:
    """Read a DecisionResult by result_id. Returns None if not found."""
    target = Path(path) if path else default_result_store_path()
    if not target.exists():
        return None
        
    with target.open("r", encoding="utf-8") as stream:
        for line in stream:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                if record.get("result_id") == result_id:
                    return record
            except json.JSONDecodeError:
                continue
    return None
