"""Shared state for microphone queue and command listening flag."""
# -*- coding: utf-8 -*-

from __future__ import annotations

from queue import Queue

audio_queue = Queue()
listening_for_command = False
