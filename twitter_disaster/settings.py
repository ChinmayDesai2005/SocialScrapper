import os
from dotenv import load_dotenv


load_dotenv()

# Scrapy settings for twitter_disaster project

BOT_NAME = "twitter_disaster"

SPIDER_MODULES = ["twitter_disaster.spiders"]
NEWSPIDER_MODULE = "twitter_disaster.spiders"

ITEM_PIPELINES = {
    'twitter_disaster.pipelines.TweetProcessingPipeline': 300,
}
# User-Agent to identify the bot
USER_AGENT = 'TwitterDisasterBot for Disaster Data Collection (+mailto:notsoimportantt2004@gmail.com)'

# Follow robots.txt rules
ROBOTSTXT_OBEY = True

# Configure JSON output
FEED_FORMAT = 'json'
FEED_URI = 'output.json'
FEEDS = {
    'tweets.json': {
        'format': 'json',
        'encoding': 'utf8',
        'store_empty': False,
        'indent': 4,
    }
}


# Rate limiting to handle API constraints
CONCURRENT_REQUESTS = 1
DOWNLOAD_DELAY = 60
RETRY_TIMES = 3
RETRY_HTTP_CODES = [429]  # Retry only on HTTP 429

# Set settings for compatibility with Asyncio
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

# In settings.py or in the spider
DUPEFILTER_CLASS = 'scrapy.dupefilters.RFPDupeFilter'  # Default filter
