from abc import ABC, abstractmethod

from src.api.models import StoryManager


class TextGenerator(ABC):
    promt: str = None

    @abstractmethod
    async def generate_story(self, promt: str = None) -> StoryManager:
        pass
