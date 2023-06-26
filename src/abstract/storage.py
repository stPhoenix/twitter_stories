import json
from abc import ABC, abstractmethod
from typing import Union

from src.api.config import CHECKPOINT_NAME
from src.api.models import CheckPoint


class Storage(ABC):
    @abstractmethod
    async def file_exists(self, file_path: str) -> bool:
        pass

    @abstractmethod
    async def delete_file(self, file_path: str) -> bool:
        pass

    @abstractmethod
    async def get_file(self, file_path: str) -> bytes:
        pass

    @abstractmethod
    async def upload_file(self, file_path: str, file: bytes, rewrite: bool = True) -> bool:
        pass

    async def get_checkpoint(self) -> Union[CheckPoint, None]:
        if not await self.file_exists(CHECKPOINT_NAME):
            return None
        data: bytes = await self.get_file(CHECKPOINT_NAME)
        decoded = data.decode(encoding="utf-8")
        data_dict = json.loads(decoded)

        return CheckPoint(**data_dict)

    async def save_checkpoint(self, checkpoint: CheckPoint) -> bool:
        data = checkpoint.json()
        data_encoded = data.encode(encoding="utf-8")

        return await self.upload_file(CHECKPOINT_NAME, data_encoded)

    async def remove_checkpoint(self) -> bool:
        return await self.delete_file(CHECKPOINT_NAME)
