# data/models/base.py

class BaseModel:
    def to_dict(self):
        return self.__dict__
