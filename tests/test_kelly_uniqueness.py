import ast
import pathlib


def test_kelly_clasico_single_definition():
    """Pergamino §1: una responsabilidad vive en un solo vector/archivo."""
    defs = []
    for p in pathlib.Path("elite").rglob("*.py"):
        if "__pycache__" in str(p):
            continue
        tree = ast.parse(p.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "kelly_clasico":
                defs.append(str(p))
    assert len(defs) == 1, f"kelly_clasico definido múltiples veces: {defs}"
