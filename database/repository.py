from abc import ABC, abstractmethod

class Repository(ABC):
    @abstractmethod
    def create(self, model):
        pass

    @abstractmethod
    def get(self, id):
        pass

    @abstractmethod
    def list(self, limit, offset):
        pass

    @abstractmethod
    def delete(self, id):
        pass

    @abstractmethod
    def update(self, model):
        pass