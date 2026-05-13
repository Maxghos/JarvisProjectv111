"""Tab management for Jarvis."""
# -*- coding: utf-8 -*-

from __future__ import annotations

import re
from typing import Tuple

import pyautogui
import pygetwindow as gw
from rapidfuzz import fuzz, process

from jarvis.core.voice import speak


INTENTS = [
	"cambiar a la pestaña uno",
	"cambiar a la pestaña dos",
	"cambiar a la pestaña tres",
	"cambiar a la pestaña cuatro",
	"cambiar a la pestaña cinco",
	"cambiar a la pestaña seis",
	"cambiar a la pestaña siete",
	"cambiar a la pestaña ocho",
	"cambiar a la pestaña nueve",
	"siguiente pestaña",
	"pestaña siguiente",
	"pestaña anterior",
	"cerrar pestaña",
	"nueva pestaña",
	"reabrir pestaña cerrada",
]

_WORD_TO_NUMBER = {
	"uno": 1,
	"una": 1,
	"primero": 1,
	"primera": 1,
	"dos": 2,
	"segundo": 2,
	"segunda": 2,
	"tres": 3,
	"tercero": 3,
	"tercera": 3,
	"cuatro": 4,
	"cuarta": 4,
	"cinco": 5,
	"quinta": 5,
	"seis": 6,
	"sexto": 6,
	"sexta": 6,
	"siete": 7,
	"septimo": 7,
	"séptimo": 7,
	"septima": 7,
	"séptima": 7,
	"ocho": 8,
	"octavo": 8,
	"octava": 8,
	"nueve": 9,
	"noveno": 9,
	"novena": 9,
}


def _speak(message: str) -> None:
	speak(message)


def _focus_chrome() -> bool:
	windows = [window for window in gw.getAllWindows() if "chrome" in (window.title or "").lower()]
	if not windows:
		_speak("No encontré Chrome abierto")
		return False

	window = windows[0]
	try:
		if window.isMinimized:
			window.restore()
		window.activate()
		window.maximize()
	except Exception:
		try:
			window.activate()
		except Exception:
			return False

	return True


def _extract_tab_number(texto: str) -> int | None:
	texto_normalizado = texto.lower()

	match = re.search(r"\b([1-9])\b", texto_normalizado)
	if match is not None:
		return int(match.group(1))

	for word, number in _WORD_TO_NUMBER.items():
		if re.search(rf"\b{re.escape(word)}\b", texto_normalizado):
			return number

	return None


def switch_to(n: int) -> None:
	if not _focus_chrome():
		return

	if 1 <= n <= 9:
		pyautogui.hotkey("ctrl", str(n))
		_speak(f"Cambiando a la pestaña {n}")
	else:
		_speak("Solo puedo cambiar pestañas del uno al nueve")


def next_tab() -> None:
	if not _focus_chrome():
		return

	pyautogui.hotkey("ctrl", "tab")
	_speak("Siguiente pestaña")


def prev_tab() -> None:
	if not _focus_chrome():
		return

	pyautogui.hotkey("ctrl", "shift", "tab")
	_speak("Pestaña anterior")


def close_tab() -> None:
	if not _focus_chrome():
		return

	pyautogui.hotkey("ctrl", "w")
	_speak("Pestaña cerrada")


def new_tab() -> None:
	if not _focus_chrome():
		return

	pyautogui.hotkey("ctrl", "t")
	_speak("Nueva pestaña")


def reopen_tab() -> None:
	if not _focus_chrome():
		return

	pyautogui.hotkey("ctrl", "shift", "t")
	_speak("Pestaña reabierta")


def match(texto: str) -> Tuple[str, float]:
	texto_normalizado = texto.lower().strip()

	result = process.extractOne(texto_normalizado, INTENTS, scorer=fuzz.partial_ratio)
	if result is None:
		return "", 0.0

	intent, score, _ = result
	return str(intent), float(score)


def handle(texto: str, intent: str) -> None:
	texto_normalizado = texto.lower().strip()

	if intent.startswith("cambiar a la pestaña"):
		number = _extract_tab_number(texto_normalizado)
		if number is None:
			_speak("¿A qué número de pestaña?")
			return
		switch_to(number)
		return

	if intent in {"siguiente pestaña", "pestaña siguiente"}:
		next_tab()
		return

	if intent == "pestaña anterior":
		prev_tab()
		return

	if intent == "cerrar pestaña":
		close_tab()
		return

	if intent == "nueva pestaña":
		new_tab()
		return

	if intent == "reabrir pestaña cerrada":
		reopen_tab()
		return

	_speak("No entendí el comando de pestañas")
