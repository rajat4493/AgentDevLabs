import sys
from pathlib import Path


def _ensure_api_on_path() -> None:
    api_root = Path(__file__).resolve().parents[1]
    api_str = str(api_root)
    if api_str not in sys.path:
        sys.path.insert(0, api_str)


_ensure_api_on_path()
