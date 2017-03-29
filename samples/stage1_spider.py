import scrapy
from scrapy_twostage.stage1.items import DownloadedPage


class QuotesDownloaderSpider(scrapy.Spider):
    name = "quotes"
    start_urls = ['http://quotes.toscrape.com/']

    def parse(self, response):
        yield DownloadedPage.from_response(response)
        for author_url in response.css("a[href*='/author/']::attr(href)").extract():
            yield scrapy.Request(
                response.urljoin(author_url),
                callback=self.parse_author,
            )

        next_page_url = response.css("li.next > a::attr(href)").extract_first()
        if next_page_url is not None:
            yield scrapy.Request(response.urljoin(next_page_url))

    def parse_author(self, response):
        yield DownloadedPage.from_response(response)
