import pytest
from unittest import mock
from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob.aio import BlobServiceClient, BlobClient
from src.api.config import AZURE_CONTAINER_NAME
from src.implementation.storage.azure import Storage

@pytest.fixture
def mock_blob_service_client():
    return mock.create_autospec(BlobServiceClient)

@pytest.fixture
def storage(mock_blob_service_client, monkeypatch):
    monkeypatch.setattr("src.implementation.storage.azure.BlobServiceClient", mock_blob_service_client)
    return Storage()

@pytest.mark.asyncio
async def test_file_exists(storage, mock_blob_service_client):
    file_path = "test.txt"
    mock_blob_client = mock.create_autospec(BlobClient)
    mock_blob_client.exists = mock.AsyncMock(return_value=True)
    mock_blob_service_client.get_blob_client.return_value = mock_blob_client
    storage.client = mock_blob_service_client

    exists = await storage.file_exists(file_path)

    assert exists is True
    mock_blob_service_client.get_blob_client.assert_called_once_with(
        container=AZURE_CONTAINER_NAME, blob=file_path
    )
    mock_blob_client.exists.assert_awaited_once()

@pytest.mark.asyncio
async def test_delete_file(storage, mock_blob_service_client):
    file_path = "test.txt"
    mock_blob_client = mock.create_autospec(BlobClient)
    mock_blob_client.delete_blob.return_value = None
    mock_blob_service_client.get_blob_client.return_value = mock_blob_client
    storage.client = mock_blob_service_client

    deleted = await storage.delete_file(file_path)

    mock_blob_client.delete_blob.assert_awaited_once_with()
    assert deleted is None


@pytest.mark.asyncio
async def test_get_file(storage, mock_blob_service_client):
    file_path = "test.txt"
    mock_blob_client = mock.create_autospec(BlobClient)
    mock_blob_client.download_blob.return_value = mock.AsyncMock()
    mock_blob_client.download_blob.return_value.readall.return_value = b"file content"
    mock_blob_service_client.get_blob_client.return_value = mock_blob_client
    storage.client = mock_blob_service_client

    file_data = await storage.get_file(file_path)

    mock_blob_client.download_blob.assert_awaited_once_with()
    assert file_data == b"file content"

@pytest.mark.asyncio
async def test_upload_file(storage, mock_blob_service_client):
    file_path = "test.txt"
    file_data = b"file content"
    mock_blob_client = mock.create_autospec(BlobClient)
    mock_blob_client.upload_blob.return_value = True
    mock_blob_service_client.get_blob_client.return_value = mock_blob_client
    storage.client = mock_blob_service_client

    uploaded = await storage.upload_file(file_path, file_data)

    assert uploaded is True
    mock_blob_service_client.get_blob_client.assert_called_once_with(
        container=AZURE_CONTAINER_NAME, blob=file_path
    )
    mock_blob_client.upload_blob.assert_awaited_once_with(
        file_data, overwrite=True
    )
