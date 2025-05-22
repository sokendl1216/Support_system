# data/repositories/base.py

class BaseRepository:
    def __init__(self, storage):
        self.storage = storage

    def get(self, id):
        raise NotImplementedError

    def save(self, obj):
        raise NotImplementedError
