"""Command matching for Jarvis."""
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any, Callable, Dict, Tuple

from rapidfuzz import fuzz, process

from .voice import speak


ModuleMatcher = Callable[[str], Tuple[str, float]]
RegisteredModule = Dict[str, Any]

_registered_modules: Dict[str, RegisteredModule] = {}


def _build_matcher(intents: list[str]) -> ModuleMatcher:
	def match(texto: str) -> Tuple[str, float]:
		if not intents:
			return "", 0.0

		result = process.extractOne(texto, intents, scorer=fuzz.WRatio)
		if result is None:
			return "", 0.0

		intent, score, _ = result
		return str(intent), float(score)

	return match


def register_module(module: Any) -> None:
	"""Register a module with its intents, handler, and matcher."""

	module_name = module.__name__.split(".")[-1]
	intents = list(getattr(module, "INTENTS", []))
	handle = getattr(module, "handle")
	match = getattr(module, "match", None) or _build_matcher(intents)

	_registered_modules[module_name] = {
		"intents": intents,
		"handle": handle,
		"match": match,
	}


def match_and_run(texto: str) -> None:
	"""Find the best matching module and execute its handler."""

	best_module_name = None
	best_intent = ""
	best_score = 0.0

	for module_name, module_data in _registered_modules.items():
		intent, score = module_data["match"](texto)
		if score > best_score:
			best_module_name = module_name
			best_intent = intent
			best_score = score

	if best_module_name is None or best_score < 60:
		speak("No entendí el comando")
		return

	_registered_modules[best_module_name]["handle"](texto, best_intent)
