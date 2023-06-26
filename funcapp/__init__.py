import logging

import azure.functions as func

from src.implementation.publisher.twitter import Publisher
from src.implementation.text_generator.openai import TextGenerator
from src.implementation.worker.azure import Worker
from src.implementation.storage.azure import Storage

logger = logging.getLogger()
logging.basicConfig(level=logging.WARNING)

logging.basicConfig(level=logging.DEBUG)


async def main(mytimer: func.TimerRequest) -> None:
    worker = Worker(text_generator=TextGenerator(), publisher=Publisher(), storage=Storage())

    await worker.exec()

    logging.info("Done")
