# core/events.py

class EventBus:
    def __init__(self):
        self._handlers = {}

    def on(self, event_name, handler):
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        self._handlers[event_name].append(handler)

    def emit(self, event_name, **kwargs):
        handlers = self._handlers.get(event_name, [])
        for handler in handlers:
            handler(**kwargs)
