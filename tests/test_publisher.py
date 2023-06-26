from datetime import datetime
from unittest import mock
import pytest
from snscrape.modules.twitter import TwitterTweetScraper, Tweet
from src.api.models import PublisherPost
from src.implementation.publisher.twitter import Publisher


class MockTwitterTweetScraper:
    def __init__(self, tweetId):
        self.tweet_id = tweetId

    def get_items(self):
        tweet = Tweet(
            url="https://twitter.com/user/status/123456789",
            date=datetime.now(),
            rawContent="Raw tweet content",
            renderedContent="Rendered tweet content",
            id=123456789,
            user=None,
            replyCount=0,
            retweetCount=0,
            likeCount=0,
            quoteCount=0,
            conversationId=0,
            lang="en",
            card=mock.Mock(options=[mock.Mock(label="Option 1", count=0), mock.Mock(label="Option 2", count=0)])
        )
        yield tweet


class MockAuthClient:
    def __init__(self, client_key, client_secret, resource_owner_key, resource_owner_secret):
        pass

    def sign(self, uri, http_method, body, headers):
        return uri, headers, body


class MockResponse:
    def __init__(self, status, data):
        self.status = status
        self.data = data

    async def json(self):
        return self.data

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    def __getitem__(self, key):
        return self.data[key]



class MockClientSession:
    def __init__(self):
        pass

    async def close(self):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    def request(self, method, url, headers, data):
        if method == 'GET':
            response = MockResponse(200, {"data": {"id": 123456789}})
        elif method == 'POST':
            response = MockResponse(201, {"data": {"id": 987654321}})
        else:
            raise NotImplementedError()

        return response


@pytest.fixture
def mock_publisher(monkeypatch):
    monkeypatch.setattr("src.implementation.publisher.twitter.TwitterTweetScraper", MockTwitterTweetScraper)

    publisher = Publisher()
    publisher.auth_client = MockAuthClient(
        client_key="TWITTER_CONSUMER_KEY",
        client_secret="TWITTER_CONSUMER_SECRET",
        resource_owner_key="TWITTER_TOKEN",
        resource_owner_secret="TWITTER_TOKEN_SECRET"
    )
    publisher.session = MockClientSession()
    return publisher


@pytest.mark.asyncio
async def test_get_post(mock_publisher):
    tweet_id = 123456789
    expected_post = PublisherPost(
        post_id=tweet_id,
        text="Raw tweet content",
        title="",
        poll_option_1_name="Option 1",
        poll_option_1_votes=0,
        poll_option_2_name="Option 2",
        poll_option_2_votes=0
    )

    post = await mock_publisher.get_post(tweet_id)

    assert post == expected_post


@pytest.mark.asyncio
async def test_make_call(mock_publisher):
    url = "tweets"
    data = "{}"
    method = "POST"
    params = {"param1": "value1", "param2": "value2"}

    response = await mock_publisher.make_call(url, data, method, params)

    assert response["data"]["id"] == 987654321


@pytest.mark.asyncio
async def test_push_post(mock_publisher):
    tweet_id = 123456789
    post = PublisherPost(
        post_id=tweet_id,
        text="Raw tweet content",
        title="",
        poll_option_1_name="Option 1",
        poll_option_1_votes=0,
        poll_option_2_name="Option 2",
        poll_option_2_votes=0
    )

    response_data = {"data": {"id": 987654321}}
    mock_response = MockResponse(201, response_data)
    mock_publisher.make_call = mock.AsyncMock(return_value=mock_response)

    poll_post_id = await mock_publisher.push_post(post)

    assert poll_post_id == response_data["data"]["id"]
