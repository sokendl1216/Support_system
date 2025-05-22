# ui/state.py

class UIState:
    def __init__(self):
        self.current_page = "home"
        self.selected_job = None
        self.settings = {}

    def set_page(self, page):
        self.current_page = page

    def set_job(self, job):
        self.selected_job = job

    def update_settings(self, key, value):
        self.settings[key] = value
