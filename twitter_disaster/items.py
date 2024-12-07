import scrapy

class TwitterDisasterItem(scrapy.Item):
    username = scrapy.Field()  # Twitter username or author ID
    post_id = scrapy.Field()  # Twitter username or author ID
    post_body = scrapy.Field()      # Tweet content
    date = scrapy.Field()      # Date and time of the tweet
    likes = scrapy.Field()     # Number of likes
    retweets = scrapy.Field()  # Number of retweets
    post_image_url = scrapy.Field()
    location = scrapy.Field()
    disaster_type = scrapy.Field()
    source = scrapy.Field()
    url = scrapy.Field()       # URL of the tweet

