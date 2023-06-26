from typing import Optional, List

from pydantic import BaseModel


class Story(BaseModel):
    tag: str
    text: str
    option_1: Optional[str]
    option_2: Optional[str]
    end: bool = False


class StoryManager(BaseModel):
    stories: List[Story]
    active_story: Story

    def __getitem__(self, key: str):
        for i in self.stories:
            if i.tag == key:
                return i
        raise KeyError(f"No {key} in stories")


class CheckPoint(BaseModel):
    post_id: int
    story_manager: StoryManager


class PublisherPost(BaseModel):
    post_id: int
    text: str
    title: str
    poll_option_1_name: Optional[str]
    poll_option_1_votes: int = 0
    poll_option_2_name: Optional[str]
    poll_option_2_votes: int = 0
    end: bool = False
