from azure.identity import DefaultAzureCredential
from azure.storage.blob.aio import BlobServiceClient

from src.api.config import AZURE_CONTAINER_NAME, AZURE_ACCOUNT_URL
from src.abstract.storage import Storage as SPI


class Storage(SPI):
    def __init__(self):
        creds = DefaultAzureCredential()
        self.client = BlobServiceClient(account_url=AZURE_ACCOUNT_URL, credential=creds)

    def get_blob_client(self, file_path: str):
        return self.client.get_blob_client(container=AZURE_CONTAINER_NAME, blob=file_path)

    async def file_exists(self, file_path: str) -> bool:
        blob_client = self.get_blob_client(file_path)
        return await blob_client.exists()

    async def delete_file(self, file_path: str) -> bool:
        blob_client = self.get_blob_client(file_path)
        return await blob_client.delete_blob()

    async def get_file(self, file_path: str) -> bytes:
        blob_client = self.get_blob_client(file_path)
        data = await blob_client.download_blob()
        return await data.readall()

    async def upload_file(self, file_path: str, file: bytes, rewrite: bool = True) -> bool:
        blob_client = self.get_blob_client(file_path)
        return await blob_client.upload_blob(data=file, overwrite=rewrite)
