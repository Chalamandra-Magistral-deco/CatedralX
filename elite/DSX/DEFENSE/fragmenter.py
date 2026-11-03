"""Safe backup helper. Copies only when explicitly invoked; never scatters to temp/cache."""
import shutil
from pathlib import Path


def backup_file(source: str, destination: str) -> Path:
    src, dst = Path(source).expanduser(), Path(destination).expanduser()
    if not src.is_file():
        raise FileNotFoundError(src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return dst
