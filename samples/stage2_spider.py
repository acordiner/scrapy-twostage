from scrapy_twostage.stage2.spiders import PickledResponseSpiderMixin, DirectorySpider


class QuotesExtractorSpider(PickledResponseSpiderMixin, DirectorySpider):
    name = "books"
    dirname = '/tmp/booksspider'

    response_rules = [
        (r"^http://quotes.toscrape.com/author/.*/$", "parse_author_page"),
        (r"^http://quotes.toscrape.com/(page/.*/)?$", "parse_book_page"),
    ]

    def parse_author_page(self, response):
        author = response.css("div.author-details")
        yield {
            'name': author.css('h3.author-title::text').extract_first().strip(),
            'birth_date': author.css("span.author-born-date::text").extract_first(),
        }

    def parse_book_page(self, response):
        for quote in response.css("div.quote"):
            yield {
                'text': quote.css("span.text::text").extract_first(),
                'author': quote.css("small.author::text").extract_first(),
                'tags': quote.css("div.tags > a.tag::text").extract()
            }
