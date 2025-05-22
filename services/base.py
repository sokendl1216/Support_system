# services/base.py

class BaseService:
    def __init__(self, repository):
        self.repository = repository

    def execute(self, *args, **kwargs):
        raise NotImplementedError
