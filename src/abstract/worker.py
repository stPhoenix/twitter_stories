from abc import ABC, abstractmethod

from src.abstract.publisher import Publisher
from src.abstract.storage import Storage
from src.abstract.text_generator import TextGenerator


class Worker(ABC):

    def __init__(self, text_generator: TextGenerator, publisher: Publisher, storage: Storage):
        self.text_generator = text_generator
        self.publisher = publisher
        self.storage = storage

    @abstractmethod
    async def exec(self):
        pass
