from __future__ import annotations

import shutil
from pathlib import Path

_BUNDLED_CODE = Path(
    "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code"
)


def code_binary() -> Path | None:
    found = shutil.which("code")
    if found:
        return Path(found)
    if _BUNDLED_CODE.exists():
        return _BUNDLED_CODE
    return None
