import asyncio
import json

from aiohttp import ClientSession
from oauthlib.oauth1 import Client as AuthClient
from snscrape.modules.twitter import TwitterTweetScraper, Tweet

from src.api.models import PublisherPost
from src.abstract.publisher import Publisher as SPI
from src.api.config import TWITTER_TOKEN, TWITTER_TOKEN_SECRET, TWITTER_CONSUMER_SECRET, TWITTER_CONSUMER_KEY, \
    POLL_DURATION_MINUTES


class Publisher(SPI):
    poll_duration: int = POLL_DURATION_MINUTES

    def __init__(self):
        self.auth_client = AuthClient(client_key=TWITTER_CONSUMER_KEY, client_secret=TWITTER_CONSUMER_SECRET,
                                      resource_owner_key=TWITTER_TOKEN, resource_owner_secret=TWITTER_TOKEN_SECRET)
        self.session = ClientSession()
        self.base_url = "https://api.twitter.com/2/"
        self.headers = {'Content-Type': 'application/json'}

    def __del__(self):
        if self.session:
            asyncio.get_event_loop().run_until_complete(self.session.close())

    async def get_post(self, post_id: int) -> PublisherPost:
        # url = f"tweets/{post_id}"
        #
        # tweet = await self.make_call(url, "{}", "GET")
        # because twitter free tire allow only create tweets - we will scrap

        scrapper = TwitterTweetScraper(tweetId=post_id)
        data = list(scrapper.get_items())
        if len(data) == 0:
            raise ValueError(f"No tweet with id {post_id} found !")

        tweet: Tweet = data[0]

        return PublisherPost(
            post_id=post_id,
            text=tweet.rawContent,
            title="",
            poll_option_1_name=tweet.card.options[0].label,
            poll_option_1_votes=tweet.card.options[0].count,
            poll_option_2_name=tweet.card.options[1].label,
            poll_option_2_votes=tweet.card.options[1].count,
        )

    async def make_call(self, url: str, data: str, method: str, params: dict = None, retry: int = 3):
        uri = self.base_url + url
        uri = uri if params is None else uri + "?" + "&".join([f"{key}={value}" for key, value in params.items()])
        headers = self.headers

        uri, headers, body = self.auth_client.sign(
            uri=uri,
            http_method=method,
            body=data,
            headers=headers
        )

        async with self.session.request(method=method, url=uri, headers=headers, data=body) as response:
            if response.status in [200, 201]:
                return await response.json()
            if response.status > 200 and retry > 0:
                await asyncio.sleep(1)
                return await self.make_call(url, data, method, params, retry - 1)
            else:
                text = await response.text()
                raise ValueError(
                    f"HTTP error {response.status} to url {uri} and body {body} \n{text} \n{response.reason}")

    async def push_post(self, post: PublisherPost) -> int:
        text = post.title + "\n" + post.text + ("\nFinal" if post.end else "\noptions in the comments")
        text = text[:279]
        body = {
            "text": text
        }
        if not post.end:
            body["poll"] = {
                "options": ["1", "2"],
                "duration_minutes": self.poll_duration
            }
        if post.post_id != -1:
            body["reply"] = {"in_reply_to_tweet_id": str(post.post_id)}

        body = json.dumps(body)

        url = "tweets"

        result = await self.make_call(url, body, "POST")
        poll_post_id = result["data"]["id"]

        if not post.end:
            options_body = json.dumps({
                "text": f"Option 1 {post.poll_option_1_name}\nOption 2 {post.poll_option_2_name}"[:279],
                "reply": {
                    "in_reply_to_tweet_id": poll_post_id
                }
            })
            options_post = await self.make_call(url, options_body, "POST")

        return poll_post_id
