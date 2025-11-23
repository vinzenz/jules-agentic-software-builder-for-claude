from typing import Any, Callable, Dict, List


class EventEmitter:
    def __init__(self):
        self._listeners: Dict[str, List[Callable[[Any], None]]] = {}

    def on(self, event: str, listener: Callable[[Any], None]):
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(listener)

    def off(self, event: str, listener: Callable[[Any], None]):
        if event in self._listeners:
            if listener in self._listeners[event]:
                self._listeners[event].remove(listener)

    def emit(self, event: str, payload: Any = None):
        if event in self._listeners:
            for listener in self._listeners[event]:
                listener(payload)
