import scrapy
import tweepy
import time
import os
from twitter_disaster.items import TwitterDisasterItem # type: ignore


class TwitterSpider(scrapy.Spider):
    name = 'X_spider'

    def __init__(self):
        bearer_token = os.environ['TWITTER_BEARER_TOKEN']
        self.client = tweepy.Client(bearer_token=bearer_token)

    def start_requests(self):

        # usernames = ["mybmc", "ndrfhq", "narendramodi", "pmoindia"]
        usernames = [] # Add usernames that need to be tagged in the posts
        keywords = ['earthquake',
                    'shake',
                    'seismic',
                    'tremor',
                    'flood',
                    'water',
                    'rain',
                    'submerge',
                    'deluge',
                    'storm',
                    'thunderstorm',
                    'hurricane',
                    'tornado',
                    'twister',
                    'fire',
                    'wildfire',
                    'blaze',
                    'flames',
                    'explosion',
                    'crash',
                    'accident',
                    'shooting',
                    'violence',
                    'bomb',
                    'building collapse']
        exclude_usernames = ['NDRFHQ', '04NDRF']    # Accounts to ignore posts from
        

        mentions_query = " OR ".join([f"@{username}" for username in usernames])
        keywords_query = " OR ".join(keywords)
        query = f"({mentions_query}) ({keywords_query}) -is:retweet -is:reply {' '.join([f'-from:{exclude_user}' for exclude_user in exclude_usernames])}"
        # query = f"({mentions_query}) -is:retweet -is:reply"

        tweet_fields = ["id", "author_id", "created_at", "text", "geo", "attachments", "public_metrics", "entities"]
        user_fields = ["location"]
        media_fields = ["preview_image_url", "url"]


        while True:
            try:
                response = self.client.search_recent_tweets(
                    query=query,
                    max_results=10,
                    tweet_fields=tweet_fields,
                    user_fields=user_fields,
                    expansions=["attachments.media_keys"],
                    media_fields=media_fields
                )

                if not response.data:
                    self.logger.info("No tweets found for the query.")
                    return
                
                tweets = response.data
                includes = response.includes if response.includes else {}

                user_dict = {user["id"]: user for user in includes.get("users", [])}
                place_dict = {place["id"]: place for place in includes.get("places", [])}
                media_dict = {media["media_key"]: media for media in includes.get("media", [])}

                for tweet in tweets:
                    
                    item = TwitterDisasterItem()

                    # Twitter username (user ID here)
                    item['username'] = str(tweet.author_id)
                    # Tweet ID
                    item['post_id'] = str(tweet.id)
                    # Tweet content
                    item['post_body'] = tweet.text
                    # Date and time of the tweet
                    item['date'] = tweet.created_at.date()
                    # Number of likes
                    item['likes'] = tweet.public_metrics['like_count']
                    # Number of retweets
                    item['retweets'] = tweet.public_metrics['retweet_count']

                    # Tweet media attachments 
                    if hasattr(tweet, "attachments") and tweet.attachments:
                        media_keys = tweet.attachments.get("media_keys", [])
                        item['post_image_url'] = None
                        for media_key in media_keys:
                            media = media_dict.get(media_key, {})
                            media_url = media.get("url") or media.get("preview_image_url")  # Choose whichever is available
                            if media_url:
                                item['post_image_url'] = media_url
                                break
                    
                    item['location'] = ""
                    if hasattr(tweet, "geo") and tweet.geo:
                        place = place_dict.get(tweet.geo.get("place_id"), {})
                        if place:
                            item['location'] = place.get('full_name') + ", " + place.get('country')

                    if tweet.author_id in user_dict:
                        user = user_dict[tweet.author_id]
                        if "location" in user:
                            item['location'] = item.get('location', "") + user['location']

                    # Tweet URL
                    item['url'] = f"https://twitter.com/{tweet.author_id}/status/{tweet.id}"
                    yield item
                break
            except tweepy.errors.TooManyRequests as e:
                # Handle rate limiting
                try:
                    reset_time = int(e.response.headers.get('x-rate-limit-reset', time.time() + 900))
                except AttributeError:
                    reset_time = time.time() + 900  # Default to 15-minute wait
                wait_time = reset_time - int(time.time()) + 10
                self.logger.info(f"Rate limit exceeded. Sleeping for {wait_time} seconds.")
                time.sleep(wait_time)
                continue
