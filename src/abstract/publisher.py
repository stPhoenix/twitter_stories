from abc import ABC, abstractmethod

from src.api.models import PublisherPost


class Publisher(ABC):

    @abstractmethod
    async def get_post(self, post_id: int) -> PublisherPost:
        pass

    @abstractmethod
    async def push_post(self, post: PublisherPost) -> int:
        pass
