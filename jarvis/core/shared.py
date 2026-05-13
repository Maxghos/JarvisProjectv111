"""Shared state for microphone queue and command listening flag."""
# -*- coding: utf-8 -*-

from __future__ import annotations

import threading

audio_queue = threading.Queue()
listening_for_command = False
