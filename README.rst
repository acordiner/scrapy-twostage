===============
scrapy-twostage
===============

Have you ever written a web scraper, only to find out after
it's been quietly scraping every day for a long time, only
to discover that there's some extra data on the pages you
should've been scraping all along?

Or a change on a website means your scraper stops working,
and you lose days or weeks of data until you can find the
time to fix it?

This library aims to solve these problems by splitting a `Scrapy
<https://scrapy.org/>`_ spider up into two asynchronous stages:

1. **Download stage** - The website is crawled, and the pages to
   be scraped are downloaded and saved to disk.
2. **Extract stage** - The pages to be scraped are loaded from disk.
   The desired data is extracted from the pages and exported (e.g. to
   a file or database).

The crawler logic for the download stage can be kept as simple
as possible, such as opening a homepage URL and performing very
simple actions such as clicking a "next page" button or submitting
a search query. This reduces the risk of the downloader breaking if
there are minor changes made to the website.

And since all of the raw data is being saved, if you ever decide to
change your extractor logic, you can simply re-run the extract stage on
all of the data that has been downloaded.

Installation
============

Downloading and installing from PyPI
------------------------------------

To install using ``pip``::

    $ pip install scrapy-twostage

Or to install using ``easy_install``::

    $ easy_install scrapy-twostage

Downloading and installing from source
--------------------------------------

Download the latest version of ``scrapy-twostage`` from
http://pypi.python.org/pypi/scrapy-twostage/.

You can install it by doing the following::

    $ tar xvfz scrapy-twostage-0.0.0.tar.gz
    $ cd scrapy-twostage-0.0.0
    # python setup.py install # as root

Using the development version
------------------------------

You can clone the git repository by doing the following::

    $ git clone git://github.com/acordiner/scrapy-twostage.git

Using scrapy-twostage
=====================

Whenever you are using ``scrapy-twostage``, you create two Scrapy
spiders - one for the *download* stage and one for
the the *extract* stage. These spiders can either be in the
same Scrapy project, or can be in two separate Scrapy projects.

Let's take the example ``QuotesSpider`` from the `scrapy
documentation <https://doc.scrapy.org/en/1.3/intro/tutorial.html>`_
as an example::

    import scrapy


    class QuotesSpider(scrapy.Spider):
        name = "quotes"
        start_urls = ['http://quotes.toscrape.com/']

        def parse(self, response):
            for quote in response.css("div.quote"):
                yield {
                    'text': quote.css("span.text::text").extract_first(),
                    'author': quote.css("small.author::text").extract_first(),
                    'tags': quote.css("div.tags > a.tag::text").extract()
                }

            next_page_url = response.css("li.next > a::attr(href)").extract_first()
            if next_page_url is not None:
                yield scrapy.Request(response.urljoin(next_page_url))

This spider is a little simplistic for our purposes, so let's quickly
extend it so that it scrapes the author bio pages as well::

    import scrapy


    class QuotesSpider(scrapy.Spider):
        name = 'quotes'
        start_urls = [
            'http://quotes.toscrape.com/',
        ]

        def parse(self, response):
            for quote in response.css("div.quote"):
                yield {
                    'text': quote.css("span.text::text").extract_first(),
                    'author': quote.css("small.author::text").extract_first(),
                    'tags': quote.css("div.tags > a.tag::text").extract()
                }
                author_url = quote.css("a[href*='/author/']::attr(href)").extract_first()
                yield scrapy.Request(
                    response.urljoin(author_url),
                    callback=self.parse_author,
                )

            next_page_url = response.xpath('//li[@class="next"]/a/@href').extract_first()
            if next_page_url is not None:
                yield scrapy.Request(response.urljoin(next_page_url))

        def parse_author(self, response):
            author = response.css("div.author-details")
            yield {
                'name': author.css('h3.author-title::text').extract_first().strip(),
                'birth_date': author.css("span.author-born-date::text").extract_first(),
            }


Now we can get to work converting this spider into a
``scrapy-twostage`` project. We need to break it up into two
Scrapy spiders; let's call the first one ``QuotesDownloaderSpider``
and the second one ``QuotesExtractorSpider``.

Stage 1: ``QuotesDownloaderSpider``
-----------------------------------

The goal of the *downloader* spider is to:

1. Crawl the website, performing whatever actions are required
   to visit every page that needs to be scraped (e.g. clicking
   links, entering search queries)
2. Yield a `DownloadedPage` object corresponding to every page
   that is to be downloaded.

To create a downloader spider that corresponds to the `QuotesSpider`,
create the following in a file called ``stage1_spider.py``::

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

You can see that the first thing we do in every request callback
function is to yield a ``DownloadedPage`` object. This is how we define
every page that we wish to download from stage 1, so that it can be
scraped in stage 2.

We also need to specify how and where to store the ``DownloadedPage``
objects, so add the following to a `Scrapy settings
<https://doc.scrapy.org/en/latest/topics/settings.html>`_ file called
``stage1_settings.py``::

    FEED_FORMAT = 'pickle'
    FEED_URI = 'file:///path/to/your/files/%(name)s/%(time)s.pickle'

Replace ``/path/to/you/files`` with a directory where you would
like to store the ``DownloadedPage`` objects. The ``%(name)s``
and ``%(time)s`` strings will be replaced with the name of the
spider (e.g. "quotes") and the timestamp when the spider runs.

.. note:: It is important that the ``FEED_URI`` ends with the
   ``.pickle`` extension.

You can then try running the stage 1 spider::

    $ SCRAPY_SETTINGS_MODULE=stage1_settings scrapy runspider stage1_spider

You can verify that it worked by checking that the directory specified
in the ``FEED_URI`` setting now contains some pickle files.

Stage 2: ``QuotesExtractorSpider``
----------------------------------

The extractor spider is responsible for scraping the pages which were
downloaded in stage one. This spider needs to:

* Inherit from the ``DirectorySpider`` base class - This type of spider can
  retrieve stored files on disk (specifically the ``DownloadedPage`` objects
  we stored in the previous stage).
* Inherit from the ``PickledResponseSpiderMixin`` mixin class - This mixin
  allows us to read the pickled ``DownloadedPage`` objects.
* Specify a ``dirname`` property, which must match the directory
  specified in the ``FEED_URI`` from step one (but excluding the
  ``file://`` prefix and the ``/%(name)s/%(time)s.pickle`` suffix).
* Specify a ``response_rules`` property, which is a list of tuples
  ``(regex, callback)``, where ``regex`` is a regular expression to
  map downloaded URLs to the callbacks used for processing the URLs.
  The ``callback`` can be a string (indicating the name of a spider
  method), a callable, or ``None`` to ignore the URL.

Here is how we might create our extractor spider::

    from scrapy_twostage.stage2.spiders import PickledResponseSpiderMixin, DirectorySpider


    class QuotesExtractorSpider(PickledResponseSpiderMixin, DirectorySpider):
        name = "books"
        dirname = '/path/to/your/files/'

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


The ``response_rules`` are matched from top to bottom.
If a URL does not match any of the rules, a ``NotImplementedError``
exception will be thrown; therefore, remember to use ``None`` as
the callback for any URLs that need to be ignored.

You can then try running the stage 2 spider::

    $ scrapy runspider stage2_spider

and you should see a bunch of scraped books and authors being
printed out. And that's it!

Compressed pickle storage
=========================

If you wish to compress the pickle files to save disk space, put this
in your settings::

    FEED_EXPORTERS = {
        'gzip-pickle': 'scrapy_twostage.stage1.GzipPickleItemExporter',
    }
    FEED_FORMAT = 'gzip-pickle'

You also ensure that your ``FEED_URI`` ends with the extension ``.pickle.gz``
(rather than ``.pickle``). For example::

    FEED_URI = 'file:///path/to/your/files/%(name)s/%(time)s.pickle.gz'

Storing images
==============

You can use Scrapy's `images pipeline feature
<https://doc.scrapy.org/en/1.1/topics/media-pipeline.html#using-the-images-pipeline>`_ in order to download images
in addition to the pages you download in stage 1. For example,
you could configure an images pipeline that saves to an AWS S3
bucket by adding this to your settings::

    ITEM_PIPELINES = {
        'scrapy.pipelines.images.ImagesPipeline': 1,
    }
    IMAGES_THUMBS = {
        'small': (64, 64),
        'large': (256, 256),
    }
    IMAGES_STORE = '/path/to/my/images/'

In your stage one scraper, you should then extract the image URLs
from the page and include them in the ``DownloadedPage``
object, e.g.::

    def parse(self, response):
        image_urls = response.selector.xpath('//img/@src').extract()
        yield DownloadedPage.from_response(response, image_urls=image_urls)

Using Amazon S3
===============

To store the downlaoded pages on `Amazon S3
<https://aws.amazon.com/s3/>`_, specify your ``FEED_URI``
in the stage one settings as an S3 URI, e.g.::

    FEED_URI = 's3://%s:%s@%s/%%(name)s/%%(time)s.pickle.gz' % (
        AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_BUCKET_NAME
    )

If you are storing images, you can use an S3 URI for the
``IMAGES_STORE`` setting too::

    IMAGES_STORE = 's3://%s/_images/' % AWS_BUCKET_NAME

Bug tracker
===========

If you have any suggestions, bug reports or annoyances please report them
at http://github.com/acordiner/scrapy-twostage/issues/

License
=======

This software is licensed under the ``GPL v2 License``. See the ``LICENSE``
file in the top distribution directory for the full license text.
