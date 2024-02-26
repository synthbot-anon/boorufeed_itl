# Overview: periodically check for new images in a booru
# Forward the results to a stream

import random
import string
from datetime import datetime, timezone

from scraper_itl import Scraper, ScraperConfig, ScraperItl


def age(iso_timestamp):
    # Parse the timestamp string to a datetime object
    timestamp = datetime.fromisoformat(iso_timestamp)
    # Ensure the timestamp is aware it's in UTC
    timestamp = timestamp.replace(tzinfo=timezone.utc)
    # Get the current time in UTC
    current_time_utc = datetime.now(timezone.utc)
    # Calculate the difference in time
    age_delta = current_time_utc - timestamp
    # Return the age in seconds
    return age_delta.total_seconds()


def randomString():
    letters = [random.choice(string.ascii_letters) for i in range(32)]
    return "".join(letters)


class PhilomenaScraperConfig(ScraperConfig):
    stream: str
    searchApi: str
    minDataAge: float
    filter: int
    query: str


class PhilomenaScraper(Scraper):
    @classmethod
    def create_message(cls, post):
        return {
            "id": post["id"],
            "created_at": post["created_at"],
            "tags": post["tags"],
            "format": post["format"],
            "representations": {
                "full": post["representations"]["full"],
                "thumb": post["representations"]["thumb"],
            },
            "sha512_hash": post["sha512_hash"],
            "orig_sha512_hash": post["orig_sha512_hash"],
        }

    @classmethod
    async def scrape_search_page(cls, session, domain, search_api, query, filter, order, page):
        """ Scrape a page of posts from the booru. This function normalizes the
        behavior of different boorus' search APIs to return a list of posts.
        """

        # Some boorus don't allow empty queries, so convert them to the negation of a
        # random tag
        query = query or f"-{randomString()}"

        # Construct the GET url
        url = (
            "https://"
            + domain
            + f"{search_api}?"
            + (f"q={query}&" if query else "")
            + f"filter_id={filter}&"
            + f"sf=created_at&"
            + f"sd={order}&"
            + f"per_page=50"
            + f"&page={page}"
        )

        response = (await session.get(url)).json()
        if not response:
            return []

        # Some boorus use "posts" and some use "images" as the key for the list of
        # posts
        if "posts" in response:
            return response["posts"]
        elif "images" in response:
            return response["images"]

    async def get_new_posts(self, domain, api, filter, query):
        """Get new posts from the booru since the last scraped, based on config.status.

        `domain`, `api`, `filter`, and `query` must be immutable when fetching new
        posts, which is why they are passed as arguments to this function. Everything
        else can be mutable, so it's fetched from self.config as it's used.
        """
        page = 1

        while True:
            posts = await PhilomenaScraper.scrape_search_page(
                self.session, domain, api, query, filter, "desc", page
            )

            if not posts:
                break

            for post in posts:
                if age(post["created_at"]) < self.config.minDataAge:
                    continue

                post_id = post["id"]
                yield post_id, PhilomenaScraper.create_message(post)

            page += 1

    async def scrape(self, itl: ScraperItl):
        domain = self.config.domain
        api = self.config.searchApi
        filter = self.config.filter
        query = self.config.query

        mostRecentPostSeen = None

        async for postId, message in self.get_new_posts(domain, api, filter, query):
            if self.config.status == None:
                # This is the first time we've scraped. Since we're only streaming
                # updates, we don't need to send the old posts to the stream. We just
                # need to remember the most recent post we've seen.
                self.config.status = postId
                return postId
            
            # The scrape results are ordered by creation date, so the first post we see
            # is going to be the most recent one. No need to use max() to find the most
            # recent post.
            mostRecentPostSeen = mostRecentPostSeen or postId

            if postId <= self.config.status:
                # We've reached a post we've seen before, so we're done.
                self.config.status = mostRecentPostSeen
                return mostRecentPostSeen
            
            itl.stream_send(
                loop="booru-streams",
                streamId=self.config.stream,
                message=message,
            )


if __name__ == "__main__":
    itl = ScraperItl(
        "loop-resources", "loop-secrets", client="scraper", cluster="boorufeed-configs"
    )
    itl.register_scraper(
        "boorufeed.synthbot.ai",
        "v1",
        "PhilomenaScraper",
        PhilomenaScraperConfig,
        PhilomenaScraper,
    )
    itl.start(daemon=False)
    itl.wait()
