import datetime

import scrapy


class DownloadedPage(scrapy.Item):
    url = scrapy.Field()
    status = scrapy.Field()
    headers = scrapy.Field()
    text = scrapy.Field()
    meta = scrapy.Field()
    flags = scrapy.Field()
    timestamp = scrapy.Field()
    image_urls = scrapy.Field()
    images = scrapy.Field()

    @classmethod
    def from_response(cls, response, timestamp=None, image_urls=None):
        kwargs = {
            'url': response.url,
            'status': response.status,
            'headers': response.headers,
            'text': response.text,
            'meta': response.text,
            'flags': response.flags,
            'timestamp': timestamp or datetime.datetime.utcnow(),
        }
        if image_urls:
            kwargs['image_urls'] = image_urls
        return cls(**kwargs)
