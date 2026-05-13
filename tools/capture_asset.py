"""Utility to capture UI assets for Jarvis modules."""
# -*- coding: utf-8 -*-

from __future__ import annotations

import sys
import time
from pathlib import Path

import pyautogui
from PIL import Image


def capture_asset(module_name: str, asset_name: str) -> Path:
    """Capture a 60x60 screenshot centered on the current mouse position."""

    print("Positiona el mouse sobre el elemento que quieres capturar.")
    for remaining in range(3, 0, -1):
        print(f"Capturando en {remaining}...")
        time.sleep(1)

    x, y = pyautogui.position()
    left = int(x - 30)
    top = int(y - 30)
    screenshot = pyautogui.screenshot(region=(left, top, 60, 60))

    output_path = Path(__file__).resolve().parent.parent / "jarvis" / "modules" / module_name / "assets" / f"{asset_name}.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    screenshot.save(output_path)

    print(f"Guardado en: {output_path}")

    image = Image.open(output_path)
    image.show()

    return output_path


def main() -> None:
    if len(sys.argv) != 3:
        script_name = Path(sys.argv[0]).name
        print(f"Uso: python {script_name} <module_name> <asset_name>")
        raise SystemExit(1)

    module_name = sys.argv[1].strip()
    asset_name = sys.argv[2].strip()
    capture_asset(module_name, asset_name)


if __name__ == "__main__":
    main()
