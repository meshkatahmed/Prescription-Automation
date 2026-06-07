import sys
from pathlib import Path


def pytest_sessionstart(session) -> None:
    root = Path(__file__).resolve().parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
