import asyncio
import logging
from unittest import mock

import pytest

from src.abstract.publisher import Publisher
from src.abstract.storage import Storage
from src.abstract.text_generator import TextGenerator
from src.api.models import CheckPoint, PublisherPost, Story, StoryManager
from src.implementation.worker.azure import Worker


@pytest.fixture
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def text_generator():
    return mock.MagicMock(spec=TextGenerator)


@pytest.fixture
def publisher():
    return mock.MagicMock(spec=Publisher)


@pytest.fixture
def storage():
    return mock.MagicMock(spec=Storage)


@pytest.fixture
def worker(text_generator, publisher, storage):
    return Worker(text_generator, publisher, storage)


@pytest.fixture(autouse=True)
def setup_logging():
    logging.basicConfig(level=logging.DEBUG)


@pytest.mark.asyncio
async def test_exec_with_checkpoint(worker, storage):
    checkpoint = CheckPoint(post_id=1, story_manager=StoryManager(stories=[], active_story=Story(tag="", text="")))
    storage.get_checkpoint = mock.AsyncMock(return_value=checkpoint)
    worker.continue_story = mock.AsyncMock()

    await worker.exec()

    storage.get_checkpoint.assert_awaited_once()
    worker.continue_story.assert_called_once_with(checkpoint)


@pytest.mark.asyncio
async def test_exec_without_checkpoint(worker, storage):
    storage.get_checkpoint = mock.AsyncMock(return_value=None)
    worker.start_new_story = mock.AsyncMock()

    await worker.exec()

    storage.get_checkpoint.assert_awaited_once()
    worker.start_new_story.assert_called_once()


@pytest.mark.asyncio
async def test_publish_new_post(worker, publisher):
    story = Story(tag="", text="Some story", option_1="Option 1", option_2="Option 2", end=False)
    publisher.push_post = mock.AsyncMock(return_value=2)

    result = await worker.publish_new_post(story, previous_post=1)

    assert result == 2
    publisher.push_post.assert_awaited_once_with(
        PublisherPost(
            post_id=1,
            text="Some story",
            title="#ai #generated #story #CHOICEISYOURS",
            poll_option_1_name="Option 1",
            poll_option_2_name="Option 2",
            end=False
        )
    )


@pytest.mark.asyncio
async def test_start_new_story(worker, text_generator, publisher, storage):
    manager = StoryManager(stories=[], active_story=Story(tag="", text="Some story", option_1="Option 1", option_2="Option 2", end=False))
    text_generator.generate_story = mock.AsyncMock(return_value=manager)
    worker.publish_new_post = mock.AsyncMock(return_value=2)
    storage.save_checkpoint = mock.AsyncMock()

    await worker.start_new_story()

    text_generator.generate_story.assert_awaited_once()
    worker.publish_new_post.assert_awaited_once_with(manager.active_story)
    storage.save_checkpoint.assert_awaited_once_with(
        CheckPoint(post_id=2, story_manager=manager)
    )


@pytest.mark.asyncio
async def test_continue_story(worker, publisher, storage):
    story_option = "1"  # Replace with the desired story option

    # Create a story with the corresponding tag
    story = Story(tag=f"story-{story_option}", text="Some text")
    story2 = Story(tag=f"story-{story_option}-1", text="Some text", end=True)
    checkpoint = CheckPoint(post_id=1, story_manager=StoryManager(stories=[story, story2], active_story=story))

    post = mock.MagicMock()
    post.poll_option_1_votes = 2
    post.poll_option_2_votes = 1
    post.post_id = 1
    publisher.get_post = mock.AsyncMock(return_value=post)
    worker.publish_new_post = mock.AsyncMock(return_value=3)
    storage.remove_checkpoint = mock.AsyncMock(return_value=True)

    await worker.continue_story(checkpoint)

    publisher.get_post.assert_called_once_with(1)
    worker.publish_new_post.assert_called_once_with(story2, post.post_id)
    storage.remove_checkpoint.assert_called_once()




@pytest.mark.asyncio
async def test_generate_story(text_generator):
    manager = StoryManager(stories=[], active_story=Story(tag="", text="Some story"))
    text_generator.generate_story = mock.AsyncMock(return_value=manager)

    result = await text_generator.generate_story()

    assert result == manager
    text_generator.generate_story.assert_awaited_once_with()

