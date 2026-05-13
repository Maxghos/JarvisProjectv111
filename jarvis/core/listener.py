"""Speech listener for Jarvis."""
# -*- coding: utf-8 -*-

from __future__ import annotations

import time
from typing import List

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

from jarvis.core import shared


_SAMPLE_RATE = 16000
_CHUNK_SECONDS = 0.5
_CHUNK_FRAMES = int(_SAMPLE_RATE * _CHUNK_SECONDS)
_SILENCE_THRESHOLD = 0.008
_MIN_CHUNK_SECONDS = 1.0
_MAX_SILENCE_SECONDS = 2.0
_MAX_AUDIO_SECONDS = 30.0

_model = WhisperModel("tiny", device="cpu", compute_type="int8")


def _is_silent(chunk: np.ndarray) -> bool:
	if chunk.size == 0:
		return True
	return float(np.max(np.abs(chunk))) < _SILENCE_THRESHOLD


def _record_audio() -> np.ndarray:
	print("[Jarvis] Grabando...")
	recorded_chunks: List[np.ndarray] = []
	silent_chunks = 0
	max_chunks = int(_MAX_AUDIO_SECONDS / _CHUNK_SECONDS)
	silence_chunks = int(_MAX_SILENCE_SECONDS / _CHUNK_SECONDS)
	min_chunks_before_silence = int(_MIN_CHUNK_SECONDS / _CHUNK_SECONDS)

	if shared.listening_for_command:
		# Consume from shared audio queue (single stream mode)
		# Accumulate small frames into proper-sized chunks for silence detection
		accumulator = np.empty(0, dtype=np.float32)
		try:
			while len(recorded_chunks) < max_chunks:
				audio_frame = shared.audio_queue.get(timeout=0.1)
				mono_chunk = np.asarray(audio_frame, dtype=np.int16).reshape(-1)
				# Convert from int16 to float32 for consistency
				mono_chunk_float = mono_chunk.astype(np.float32) / 32768.0
				
				# Accumulate frames until we have a full chunk
				accumulator = np.concatenate([accumulator, mono_chunk_float])
				
				if len(accumulator) >= _CHUNK_FRAMES:
					# We have a full chunk - check silence and add to recorded_chunks
					full_chunk = accumulator[:_CHUNK_FRAMES]
					accumulator = accumulator[_CHUNK_FRAMES:]
					recorded_chunks.append(full_chunk)
					
					if len(recorded_chunks) > min_chunks_before_silence and _is_silent(full_chunk):
						silent_chunks += 1
						if silent_chunks >= silence_chunks:
							break
					else:
						silent_chunks = 0
			
			# Add any remaining accumulated samples after loop ends
			if len(accumulator) > 0 and recorded_chunks:
				recorded_chunks.append(accumulator)
		except Exception as e:
			print(f"[Jarvis] Error consumiendo del queue: {e}")
			if not recorded_chunks:
				return np.empty(0, dtype=np.float32)
	else:
		# Fallback: open own stream (legacy mode)
		try:
			with sd.InputStream(samplerate=_SAMPLE_RATE, channels=1, dtype="float32") as stream:
				for _ in range(max_chunks):
					audio_chunk, _ = stream.read(_CHUNK_FRAMES)
					mono_chunk = np.asarray(audio_chunk, dtype=np.float32).reshape(-1)
					recorded_chunks.append(mono_chunk)

					if len(recorded_chunks) > min_chunks_before_silence and _is_silent(mono_chunk):
						silent_chunks += 1
						if silent_chunks >= silence_chunks:
							break
					else:
						silent_chunks = 0
		except sd.PortAudioError as e:
			print(f"[Jarvis] Error de micrófono: {e}")
			return np.empty(0, dtype=np.float32)

	if not recorded_chunks:
		return np.empty(0, dtype=np.float32)

	print(f"[Jarvis] Chunks grabados: {len(recorded_chunks)}")
	return np.concatenate(recorded_chunks)


def listen() -> str:
	"""Record from the microphone and return Spanish transcription in lowercase."""

	try:
		audio = _record_audio()
	except sd.PortAudioError:
		return ""

	if audio.size == 0:
		return ""

	segments, _ = _model.transcribe(audio, language="es", vad_filter=False)
	transcription = " ".join(segment.text.strip() for segment in segments).strip().lower()
	print(f"[Jarvis] Transcripción: '{transcription}'")
	return transcription
