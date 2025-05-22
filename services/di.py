# services/di.py

class DIContainer:
    def __init__(self):
        self._providers = {}

    def register(self, key, provider):
        self._providers[key] = provider

    def resolve(self, key):
        provider = self._providers.get(key)
        if provider is None:
            raise Exception(f"No provider registered for {key}")
        return provider()
