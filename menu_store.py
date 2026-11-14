"""JSON persistence for the button menu editor."""

from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any

from .menu_model import DEFAULT_MENU, normalize


class MenuStore:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict[str, Any]:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (FileNotFoundError, OSError, ValueError):
            return deepcopy(DEFAULT_MENU)
        return normalize(raw)

    def save(self, raw: Any) -> dict[str, Any]:
        config = normalize(raw)
        temp = self.path.with_suffix(".tmp")
        temp.write_text(
            json.dumps(config, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(temp, self.path)
        return config
