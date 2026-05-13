"""Spotify automation for Jarvis."""
# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Optional, Tuple

import pyautogui
import pygetwindow as gw
from rapidfuzz import fuzz, process

from jarvis.core.voice import speak


_MODULE_DIR = Path(__file__).resolve().parent
_ASSETS_DIR = _MODULE_DIR / "assets"

INTENTS = [
	"abre spotify",
	"abrir spotify",
	"abre spotify por favor",
	"reproduce o pausa la música",
	"pausa o reproduce spotify",
	"siguiente canción",
	"salta a la siguiente canción",
	"canción anterior",
	"vuelve a la canción anterior",
	"busca una canción",
	"buscar canción",
	"sube el volumen",
	"baja el volumen",
]

_OPEN_WORDS = {"abre spotify", "abrir spotify", "abre spotify por favor"}
_PLAY_PAUSE_WORDS = {"reproduce o pausa la música", "pausa o reproduce spotify"}
_NEXT_WORDS = {"siguiente canción", "salta a la siguiente canción"}
_PREV_WORDS = {"canción anterior", "vuelve a la canción anterior"}
_SEARCH_WORDS = {"busca una canción", "buscar canción"}
_VOLUME_UP_WORDS = {"sube el volumen"}
_VOLUME_DOWN_WORDS = {"baja el volumen"}


def _confirm(message: str) -> None:
	speak(message)


def _asset_path(filename: str) -> Path:
	return _ASSETS_DIR / filename


def _click_asset(filename: str) -> bool:
	image_path = _asset_path(filename)
	if not image_path.exists():
		return False

	location = pyautogui.locateOnScreen(str(image_path), confidence=0.8)
	if location is None:
		return False

	center = pyautogui.center(location)
	pyautogui.click(center.x, center.y)
	return True


def _is_open() -> bool:
	return any("spotify" in (window.title or "").lower() for window in gw.getAllWindows())


def _focus() -> bool:
	windows = [window for window in gw.getAllWindows() if "spotify" in (window.title or "").lower()]
	if not windows:
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


def _launch_spotify() -> bool:
	candidates = [
		os.path.join(os.environ.get("APPDATA", ""), "Spotify", "Spotify.exe"),
		os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WindowsApps", "Spotify.exe"),
		os.path.join(os.environ.get("PROGRAMFILES", ""), "Spotify", "Spotify.exe"),
		os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), "Spotify", "Spotify.exe"),
	]

	for candidate in candidates:
		if candidate and os.path.isfile(candidate):
			subprocess.Popen([candidate], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
			return True

	try:
		os.startfile("spotify:")
		return True
	except OSError:
		return False


def open_spotify() -> None:
	if _is_open():
		_focus()
		_confirm("Spotify listo")
		return

	if _launch_spotify():
		_confirm("Abriendo Spotify")
		return

	_confirm("No pude abrir Spotify")


def play_pause() -> None:
	if not _is_open():
		open_spotify()
		return

	_focus()
	if not _click_asset("btn_play.png"):
		pyautogui.press("space")
	_confirm("Listo")


def next_track() -> None:
	if not _is_open():
		open_spotify()
		return

	_focus()
	if not _click_asset("btn_next.png"):
		pyautogui.hotkey("ctrl", "right")
	_confirm("Siguiente")


def prev_track() -> None:
	if not _is_open():
		open_spotify()
		return

	_focus()
	if not _click_asset("btn_prev.png"):
		pyautogui.hotkey("ctrl", "left")
	_confirm("Anterior")


def search(query: str) -> None:
	if not _is_open():
		open_spotify()

	_focus()
	pyautogui.hotkey("ctrl", "l")
	pyautogui.write(query, interval=0.02)
	pyautogui.press("enter")
	_confirm(f"Buscando {query}")


def volume_up() -> None:
	if not _is_open():
		open_spotify()
		return

	_focus()
	pyautogui.hotkey("ctrl", "up")
	_confirm("Subiendo volumen")


def volume_down() -> None:
	if not _is_open():
		open_spotify()
		return

	_focus()
	pyautogui.hotkey("ctrl", "down")
	_confirm("Bajando volumen")


def match(texto: str) -> Tuple[str, float]:
	result = process.extractOne(texto.lower().strip(), INTENTS, scorer=fuzz.partial_ratio)
	if result is None:
		return "", 0.0

	intent, score, _ = result
	return str(intent), float(score)


def handle(texto: str, intent: str) -> None:
	texto_normalizado = texto.lower().strip()

	if intent in _OPEN_WORDS:
		open_spotify()
		return

	if intent in _PLAY_PAUSE_WORDS:
		play_pause()
		return

	if intent in _NEXT_WORDS:
		next_track()
		return

	if intent in _PREV_WORDS:
		prev_track()
		return

	if intent in _SEARCH_WORDS:
		query = texto_normalizado
		
		# Extract query by splitting on search keywords
		keywords = ["busca", "buscar", "pon", "reproduce", "ponme"]
		for keyword in keywords:
			if keyword in query:
				query = query.split(keyword, 1)[1].strip()
				break
		
		# Remove common filler words from the start
		fillers = ["la canción", "el tema", "una canción llamada", "que se llama"]
		for filler in fillers:
			if query.startswith(filler):
				query = query.replace(filler, "", 1).strip()
				break
		
		if query:
			search(query)
		else:
			_confirm("Dime qué canción buscar")
		return

	if intent in _VOLUME_UP_WORDS:
		volume_up()
		return

	if intent in _VOLUME_DOWN_WORDS:
		volume_down()
		return

	_confirm("No entendí ese comando de Spotify")
