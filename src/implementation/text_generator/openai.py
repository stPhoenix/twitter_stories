import logging
import re
from typing import List

import openai

from src.abstract.text_generator import TextGenerator as SPI
from src.api.config import AZURE_OPENAI_KEY
from src.api.models import StoryManager, Story


class TextGenerator(SPI):
    promt = """
    Your goal is to write short tricky situations. These stories are split into 3 parts, where at the end of the first
    two parts you present readers with two options on how to proceed. Only after a second response, you will finish the
    story. Options should be no longer that 25 characters. No conclusions in the end.

    Write a story in the format replacing keywords in brackets with actual values. Do not change formatting of output: 
    {story-begin}: 
    \n

    {option 1}:
    \n

    {option 2}:
    \n

    {story-option 1}:
    \n

    {option 1}:
    \n

    {option 2}:
    \n

    {end-option 1}:
    \n

    {end-option 2}:
    \n

    {story-option 2}:
    \n

    {option 1}:
    \n

    {option 2}:
    \n

    {end-option 1}:
    \n

    {end-option 2}:
    \n
    """

    pattern = "\s*.*{story-begin}:\s*(?P<storybegin>\s*.+)\s*{option 1}:\s*(?P<option1>\s*.+)\s*{option 2}:\s*(?P<option2>\s*.+)\s*{story-option 1}:\s*(?P<story1>\s*.+)\s*{option 1}:\s*(?P<story1option1>\s*.+)\s*{option 2}:\s*(?P<story1option2>\s*.+)\s*{end-option 1}:\s*(?P<end11>\s*.+)\s*{end-option 2}:\s*(?P<end12>\s*.+)\s*{story-option 2}:\s*(?P<story2>\s*.+)\s*{option 1}:\s*(?P<story2option1>\s*.+)\s*{option 2}:\s*(?P<story2option2>\s*.+)\s*{end-option 1}:\s*(?P<end21>\s*.+)\s*{end-option 2}:\s*(?P<end22>\s*.+)"
    retry = 3

    def __init__(self):
        super(TextGenerator, self).__init__()
        # openai.api_type = "azure"
        # openai.api_base = AZURE_OPENAI_ENDPOINT
        # openai.api_version = "2023-05-15"
        openai.api_key = AZURE_OPENAI_KEY

    def get_content(self, promt: str = None) -> str:
        content = self.get_gpt_story(promt)
        content = content.replace("\n ", "")
        return content

    async def generate_story(self, promt: str = None) -> StoryManager:
        content = self.get_content(promt)
        names = self.search_story_parts(content)

        stories = self.compile_stories(names)

        return StoryManager(
            stories=stories,
            active_story=stories[0]
        )

    def check_empty_text(self, text: str) -> str:
        if text == "" or text == " ":
            return "No possible options - end of story"
        return text

    def compile_stories(self, names: dict) -> List[Story]:
        return [
            Story(
                tag="story",
                text=names["storybegin"],
                option_1=names["option1"],
                option_2=names["option2"],
            ),
            Story(
                tag="story-1",
                text=names["story1"],
                option_1=names["story1option1"],
                option_2=names["story1option2"],
            ),
            Story(
                tag="story-1-1",
                text=self.check_empty_text(names["end11"]),
                end=True
            ),
            Story(
                tag="story-1-2",
                text=self.check_empty_text(names["end12"]),
                end=True
            ),
            Story(
                tag="story-2",
                text=names["story2"],
                option_1=names["story2option1"],
                option_2=names["story2option2"],
            ),
            Story(
                tag="story-2-1",
                text=self.check_empty_text(names["end21"]),
                end=True
            ),
            Story(
                tag="story-2-2",
                text=self.check_empty_text(names["end22"]),
                end=True
            ),
        ]

    def search_story_parts(self, content: str) -> dict:
        groups = re.search(self.pattern, content)

        if groups:
            names: dict = groups.groupdict()
            for item in names.values():
                item = item.replace("\n\n", "").replace("\n", "")
        elif not groups and self.retry > 0:
            logging.warning("Failed to parse response. Will try with default promt")
            self.retry -= 1
            new_content = self.get_content(self.promt)
            return self.search_story_parts(new_content)
        else:
            raise ValueError(f"Can't parse response : {content}")

        return names

    def get_gpt_story(self, promt: str = None) -> str:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a writer like a greek philosopher Aristotle"},
                {"role": "user", "content": self.promt if promt is None else promt}
            ]
        )
        return response['choices'][0]['message']['content']
