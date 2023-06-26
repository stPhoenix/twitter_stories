import asyncio
import logging

from implementation.publisher.twitter import Publisher
from implementation.text_generator.openai import TextGenerator
from implementation.worker.azure import Worker
from src.implementation.storage.azure import Storage

logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
    worker = Worker(text_generator=TextGenerator(), publisher=Publisher(), storage=Storage())

    asyncio.get_event_loop().run_until_complete(worker.exec())

    print("Done")
