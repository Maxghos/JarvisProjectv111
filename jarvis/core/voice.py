"""Voice output for Jarvis."""
# -*- coding: utf-8 -*-

from __future__ import annotations

import pyttsx3


_engine = pyttsx3.init()
_engine.setProperty("rate", 175)
_engine.setProperty("volume", 1.0)

_voices = _engine.getProperty("voices")
_selected_voice_name = "voz predeterminada"

for _voice in _voices:
	_voice_name = getattr(_voice, "name", "")
	_voice_id = getattr(_voice, "id", "")
	_voice_search = f"{_voice_name} {_voice_id}".lower()
	if any(keyword in _voice_search for keyword in ("spanish", "es-", "helena", "sabina", "pablo")):
		_engine.setProperty("voice", _voice.id)
		_selected_voice_name = _voice_name or _voice.id
		break
else:
	if _voices:
		_voice = _voices[0]
		_engine.setProperty("voice", _voice.id)
		_selected_voice_name = getattr(_voice, "name", _voice.id)

print(f"[Jarvis] Voz seleccionada: {_selected_voice_name}")


def speak(text: str) -> None:
	"""Speak the provided text out loud using the local system voice."""

	_engine.say(text)
	_engine.runAndWait()
