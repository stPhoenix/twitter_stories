import json

import pytest
from unittest import mock

from api.models import StoryManager
from src.implementation.text_generator.openai import TextGenerator


@pytest.fixture
def mock_openai_chat_completion():
    return mock.patch("src.implementation.text_generator.openai.openai.ChatCompletion")


@pytest.fixture
def text_generator(mock_openai_chat_completion):
    with mock_openai_chat_completion as mock_chat_completion:
        yield TextGenerator()


@pytest.mark.asyncio
async def test_generate_story(text_generator, mock_openai_chat_completion):
    mock_response =  """
Here's an example:

    {story-begin}: 
    You find a wallet on the street. It contains $500. Do you:
    
    {option 1}: Turn it into the police
    
    {option 2}: Keep the money
    
    {story-option 1}: 
    You turn the wallet into the police station. Later, the owner calls and rewards you with $100. Do you:
    
    {option 1}: Accept the reward
    
    {option 2}: Refuse the reward
    
    {end-option 1}: 
    You accept the reward and feel good about making an honest decision.
    
    {end-option 2}: 
    You refuse the reward but feel satisfied knowing you did the right thing.
    
    {story-option 2}: 
    You keep the money and feel guilty. Later, you see a homeless person and have an urge to help. Do you:
    
    {option 1}: Give the homeless person some money
    
    {option 2}: Ignore the homeless person and move on
    
    {end-option 1}: 
    You give the homeless person some money and feel better about yourself.
    
    {end-option 2}: 
    You ignore the homeless person and feel bad about your decision.
                    """
    ready_dict = {'stories': [{'tag': 'story', 'text': 'You find a wallet on the street. It contains $500. Do you:', 'option_1': 'Turn it into the police', 'option_2': 'Keep the money', 'end': False}, {'tag': 'story-1', 'text': 'You turn the wallet into the police station. Later, the owner calls and rewards you with $100. Do you:', 'option_1': 'Accept the reward', 'option_2': 'Refuse the reward', 'end': False}, {'tag': 'story-1-1', 'text': 'You accept the reward and feel good about making an honest decision.', 'option_1': None, 'option_2': None, 'end': True}, {'tag': 'story-1-2', 'text': 'You refuse the reward but feel satisfied knowing you did the right thing.', 'option_1': None, 'option_2': None, 'end': True}, {'tag': 'story-2', 'text': 'You keep the money and feel guilty. Later, you see a homeless person and have an urge to help. Do you:', 'option_1': 'Give the homeless person some money', 'option_2': 'Ignore the homeless person and move on', 'end': False}, {'tag': 'story-2-1', 'text': 'You give the homeless person some money and feel better about yourself.', 'option_1': None, 'option_2': None, 'end': True}, {'tag': 'story-2-2', 'text': 'You ignore the homeless person and feel bad about your decision.', 'option_1': None, 'option_2': None, 'end': True}], 'active_story': {'tag': 'story', 'text': 'You find a wallet on the street. It contains $500. Do you:', 'option_1': 'Turn it into the police', 'option_2': 'Keep the money', 'end': False}}
    
    example = StoryManager(**ready_dict)
    
    text_generator.get_content = mock.MagicMock(return_value=mock_response)

    story_manager = await text_generator.generate_story()

    assert story_manager == example


def test_search_story_parts(text_generator):
    content = """
Here's an example:

    {story-begin}: 
    You find a wallet on the street. It contains $500. Do you:
    
    {option 1}: Turn it into the police
    
    {option 2}: Keep the money
    
    {story-option 1}: 
    You turn the wallet into the police station. Later, the owner calls and rewards you with $100. Do you:
    
    {option 1}: Accept the reward
    
    {option 2}: Refuse the reward
    
    {end-option 1}: 
    You accept the reward and feel good about making an honest decision.
    
    {end-option 2}: 
    You refuse the reward but feel satisfied knowing you did the right thing.
    
    {story-option 2}: 
    You keep the money and feel guilty. Later, you see a homeless person and have an urge to help. Do you:
    
    {option 1}: Give the homeless person some money
    
    {option 2}: Ignore the homeless person and move on
    
    {end-option 1}: 
    You give the homeless person some money and feel better about yourself.
    
    {end-option 2}: 
    You ignore the homeless person and feel bad about your decision.
    """
    names = text_generator.search_story_parts(content)

    assert names["storybegin"] == 'You find a wallet on the street. It contains $500. Do you:'
    assert names["option1"] == 'Turn it into the police'
    assert names["option2"] == 'Keep the money'
    assert names["story1"] == 'You turn the wallet into the police station. Later, the owner calls and rewards you with $100. Do you:'
    assert names["story1option1"] == 'Accept the reward'
    assert names["story1option2"] == 'Refuse the reward'
    assert names["end11"] == 'You accept the reward and feel good about making an honest decision.'
    assert names["end12"] == 'You refuse the reward but feel satisfied knowing you did the right thing.'
    assert names["story2"] == 'You keep the money and feel guilty. Later, you see a homeless person and have an urge to help. Do you:'
    assert names["story2option1"] == 'Give the homeless person some money'
    assert names["story2option2"] == 'Ignore the homeless person and move on'
    assert names["end21"] == 'You give the homeless person some money and feel better about yourself.'
    assert names["end22"] == 'You ignore the homeless person and feel bad about your decision.'


def test_compile_stories(text_generator):
    names = {
        "storybegin": "Story 1",
        "option1": "Option 1",
        "option2": "Option 2",
        "story1": "Story Option 1",
        "story1option1": "Option 1",
        "story1option2": "Option 2",
        "end11": "End Option 1",
        "end12": "End Option 2",
        "story2": "Story Option 2",
        "story2option1": "Option 1",
        "story2option2": "Option 2",
        "end21": "End Option 1",
        "end22": "End Option 2",
    }

    stories = text_generator.compile_stories(names)

    assert len(stories) == 7
    assert stories[0].tag == "story"
    assert stories[0].text == "Story 1"
    assert stories[0].option_1 == "Option 1"
    assert stories[0].option_2 == "Option 2"
    assert stories[1].tag == "story-1"
    assert stories[1].text == "Story Option 1"
    assert stories[1].option_1 == "Option 1"
    assert stories[1].option_2 == "Option 2"
    assert stories[2].tag == "story-1-1"
    assert stories[2].text == "End Option 1"
    assert stories[2].end is True
    assert stories[3].tag == "story-1-2"
    assert stories[3].text == "End Option 2"
    assert stories[3].end is True
    assert stories[4].tag == "story-2"
    assert stories[4].text == "Story Option 2"
    assert stories[4].option_1 == "Option 1"
    assert stories[4].option_2 == "Option 2"
    assert stories[5].tag == "story-2-1"
    assert stories[5].text == "End Option 1"
    assert stories[5].end is True
    assert stories[6].tag == "story-2-2"
    assert stories[6].text == "End Option 2"
    assert stories[6].end is True


def test_check_empty_text(text_generator):
    empty_text = ""
    whitespace_text = " "
    non_empty_text = "Some text"

    assert text_generator.check_empty_text(empty_text) == "No possible options - end of story"
    assert text_generator.check_empty_text(whitespace_text) == "No possible options - end of story"
    assert text_generator.check_empty_text(non_empty_text) == non_empty_text


def test_get_content(text_generator, mock_openai_chat_completion):
    text_generator.get_gpt_story = mock.MagicMock(return_value="Generated story content")

    content = text_generator.get_content()

    assert content == "Generated story content"

