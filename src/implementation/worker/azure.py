import logging

from src.abstract.worker import Worker as SPI
from src.api.models import CheckPoint, PublisherPost, Story

logger = logging.getLogger(__name__)


class Worker(SPI):
    async def exec(self):
        logger.info("Getting checkpoint")
        checkpoint = await self.storage.get_checkpoint()

        if checkpoint:
            logger.debug(f"Checkpoint: {checkpoint.dict()}")
            return await self.continue_story(checkpoint)
        else:
            return await self.start_new_story()

    async def publish_new_post(self, story: Story, previous_post: int = -1) -> int:
        logging.info(f"Publishing post {story.text}")
        title = "#ai #generated #story #CHOICEISYOURS"

        post = PublisherPost(
            post_id=previous_post,
            text=story.text,
            title=title,
            poll_option_1_name=story.option_1,
            poll_option_2_name=story.option_2,
            end=story.end
        )
        return await self.publisher.push_post(post)

    async def start_new_story(self) -> None:
        logging.info("Starting new story")
        manager = await self.text_generator.generate_story()

        post_id = await self.publish_new_post(manager.active_story)

        checkpoint = CheckPoint(
            post_id=post_id,
            story_manager=manager
        )

        await self.storage.save_checkpoint(checkpoint)

    async def continue_story(self, checkpoint: CheckPoint) -> None:
        logging.info("Continue story")
        post = await self.publisher.get_post(checkpoint.post_id)

        story_option = "1" if post.poll_option_1_votes > post.poll_option_2_votes else "2"
        next_story = checkpoint.story_manager[f"{checkpoint.story_manager.active_story.tag}-{story_option}"]

        post_id = await self.publish_new_post(next_story, post.post_id)

        checkpoint.story_manager.active_story = next_story
        checkpoint.post_id = post_id

        if next_story.end:
            await self.storage.remove_checkpoint()
        else:
            await self.storage.save_checkpoint(checkpoint)
