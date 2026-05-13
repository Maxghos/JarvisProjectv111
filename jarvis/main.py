"""Jarvis entry point."""
# -*- coding: utf-8 -*-

from __future__ import annotations

import importlib
import sys
import threading
import time
from pathlib import Path

import numpy as np
import sounddevice as sd
from openwakeword.model import Model
from rapidfuzz import fuzz, process

if __package__ in {None, ""}:
	project_root = Path(__file__).resolve().parent.parent
	if str(project_root) not in sys.path:
		sys.path.insert(0, str(project_root))

from jarvis.core.listener import listen
from jarvis.core.matcher import match_and_run, register_module
from jarvis.core.voice import speak
from jarvis.core import shared


_WAKE_WORD_THRESHOLD = 0.1
_WAKE_WORD_FRAME_SIZE = 1280
_SAMPLE_RATE = 16000
_SLEEP_PHRASES = [
	"gracias por tu servicio",
	"hasta luego jarvis",
	"descansa",
]

try:
	_wake_word_model = Model(inference_framework="onnx")
except Exception as e:
	print(f"[Jarvis] Error cargando wake word model: {e}")
	print("[Jarvis] Descargá el modelo desde: https://github.com/dscripka/openWakeWord")
	sys.exit(1)

_assistant_active = threading.Event()
_shutdown_event = threading.Event()


def _audio_callback(indata, frames, time_info, status):
	"""Callback for audio stream - puts frames into shared queue."""
	if status:
		print(f"[Jarvis] Audio callback error: {status}")
	shared.audio_queue.put(indata.copy())


def _discover_and_register_modules() -> None:
	modules_dir = Path(__file__).resolve().parent / "modules"
	for child in sorted(modules_dir.iterdir()):
		if not child.is_dir():
			continue

		module_file = child / f"{child.name}.py"
		if not module_file.exists():
			continue

		module_name = f"jarvis.modules.{child.name}.{child.name}"
		module = importlib.import_module(module_name)

		required_attributes = ("INTENTS", "match", "handle")
		if not all(hasattr(module, attribute) for attribute in required_attributes):
			continue

		register_module(module)


def _sleep_phrase_score(texto: str) -> tuple[str, float]:
	result = process.extractOne(texto, _SLEEP_PHRASES, scorer=fuzz.WRatio)
	if result is None:
		return "", 0.0

	phrase, score, _ = result
	return str(phrase), float(score)


def _handle_transcription(texto: str) -> None:
	if not texto:
		return

	sleep_phrase, score = _sleep_phrase_score(texto)
	if score > 80:
		speak("Cuando me necesites, aquí estaré")
		return

	match_and_run(texto)


def _listen_for_wake_word() -> None:
	"""Listen for wake word from single shared microphone stream."""
	_keys_printed = False
	
	# Open ONE stream with callback - stays open forever
	with sd.InputStream(samplerate=_SAMPLE_RATE, channels=1, dtype="int16", 
	                     blocksize=_WAKE_WORD_FRAME_SIZE, callback=_audio_callback):
		while not _shutdown_event.is_set():
			if not shared.listening_for_command:
				# Wake word detection mode - pull from queue and analyze
				try:
					audio_frame = shared.audio_queue.get(timeout=0.1)
				except:
					continue
				
				frame = np.asarray(audio_frame, dtype=np.int16).reshape(-1)
				predictions = _wake_word_model.predict(frame)
				
				if not _keys_printed:
					print(f"[wake] available keys: {list(predictions.keys())}")
					_keys_printed = True
				
				best_key = None
				best_score = 0.0
				for key, value in predictions.items():
					float_value = float(value)
					if float_value > 0.05:
						print(f"[wake] {key}: {float_value:.3f}")
					if float_value > best_score:
						best_score = float_value
						best_key = key
				
				if best_score >= _WAKE_WORD_THRESHOLD and not _assistant_active.is_set():
					# Wake word detected!
					_assistant_active.set()
					if best_key:
						print(f"[Jarvis] Activado por: {best_key}")
					
					# Clear queue for fresh listening
					while not shared.audio_queue.empty():
						try:
							shared.audio_queue.get_nowait()
						except:
							break
					
					# Signal that we're listening for command
					shared.listening_for_command = True
					
					# Speak and listen
					t = threading.Thread(target=speak, args=("Dime",))
					t.start()
					t.join()
					print("[Jarvis] Hablando: Dime")
					time.sleep(1.0)
					
					texto = listen()
					print(f"[Jarvis] Escuché: '{texto}'")
					_handle_transcription(texto)
					
					shared.listening_for_command = False
					_assistant_active.clear()
					time.sleep(0.5)
					print("[Jarvis] Volviendo a escuchar...")
			else:
				# Waiting for listen() to finish - drain queue
				try:
					shared.audio_queue.get_nowait()
				except:
					pass
				time.sleep(0.01)


def main() -> None:
	_discover_and_register_modules()

	wake_thread = threading.Thread(target=_listen_for_wake_word, daemon=True)
	wake_thread.start()

	try:
		while not _shutdown_event.is_set():
			time.sleep(0.5)
	except KeyboardInterrupt:
		_shutdown_event.set()


if __name__ == "__main__":
	main()
