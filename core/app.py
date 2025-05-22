# core/app.py

from core.settings import Settings
from core.events import EventBus
from core.exceptions import AppException

class Application:
    def __init__(self):
        self.settings = Settings()
        self.event_bus = EventBus()

    def run(self):
        try:
            self.event_bus.emit('APP_INITIALIZED')
            # ...アプリケーションの起動処理...
        except AppException as e:
            print(f"Application error: {e}")
            self.event_bus.emit('ERROR_OCCURRED', error=e)
        finally:
            self.event_bus.emit('APP_SHUTDOWN')

if __name__ == "__main__":
    app = Application()
    app.run()
