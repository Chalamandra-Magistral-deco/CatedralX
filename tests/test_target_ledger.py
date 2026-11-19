import json

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from targets.ledger import (
    GENESIS_HASH,
    LedgerError,
    agregar_entrada,
    verificar_cadena,
)


def _keys():
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    return private, {"clave-firma-001": public}


def _empty_ledger(path):
    path.write_text(json.dumps({
        "formato": "LEDGER_INMUTABLE_ENCADENADO_v1.0",
        "version_esquema": "1.0",
        "inicio_registro": "2026-11-18T23:22:00-06:00",
        "hash_genesis": GENESIS_HASH,
        "ultimo_hash": GENESIS_HASH,
        "entradas": [],
    }), encoding="utf-8")


def test_append_and_verify_chain(tmp_path):
    path = tmp_path / "ledger.json"
    _empty_ledger(path)
    private, public = _keys()

    entry = agregar_entrada(
        path,
        tipo="ciclo_iniciado",
        contenido={"ciclo": 1, "estado": "iniciado"},
        timestamp="2026-11-18T23:22:00-06:00",
        clave_autorizada_id="clave-firma-001",
        clave_privada=private,
        claves_publicas=public,
    )

    ledger = json.loads(path.read_text(encoding="utf-8"))
    assert entry["id"] == "evt-0000001"
    assert ledger["ultimo_hash"] == entry["entrada_hash"]
    assert verificar_cadena(ledger, public) == (True, "Cadena completa verificada", -1)


def test_second_entry_chains_to_first(tmp_path):
    path = tmp_path / "ledger.json"
    _empty_ledger(path)
    private, public = _keys()
    args = {
        "tipo": "ciclo",
        "contenido": {"n": 1},
        "timestamp": "2026-11-18T23:22:00-06:00",
        "clave_autorizada_id": "clave-firma-001",
        "clave_privada": private,
        "claves_publicas": public,
    }
    first = agregar_entrada(path, **args)
    args["contenido"] = {"n": 2}
    second = agregar_entrada(path, **args)
    assert second["id"] == "evt-0000002"
    assert second["hash_anterior"] == first["entrada_hash"]


def test_tampered_content_is_rejected_before_append(tmp_path):
    path = tmp_path / "ledger.json"
    _empty_ledger(path)
    private, public = _keys()
    entry = agregar_entrada(
        path,
        tipo="ciclo",
        contenido={"valor": 1},
        timestamp="2026-11-18T23:22:00-06:00",
        clave_autorizada_id="clave-firma-001",
        clave_privada=private,
        claves_publicas=public,
    )
    ledger = json.loads(path.read_text(encoding="utf-8"))
    ledger["entradas"][0]["contenido"]["valor"] = 2
    path.write_text(json.dumps(ledger), encoding="utf-8")
    with pytest.raises(LedgerError, match="No se puede anexar"):
        agregar_entrada(
            path,
            tipo="siguiente",
            contenido={},
            timestamp="2026-11-18T23:23:00-06:00",
            clave_autorizada_id="clave-firma-001",
            clave_privada=private,
            claves_publicas=public,
        )
