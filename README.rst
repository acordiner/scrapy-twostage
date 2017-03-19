===============
scrapy-twostage
===============

Have you ever written a web scraper, only to find out after
a long time that there's some extra data on the pages you
should've been scraping all along?

Or a change on a website means your scraper stops working,
and you lose days or weeks of data until you can find the
time to fix it?

This library aims to solve this problem by splitting a `Scrapy
<https://scrapy.org/>`_ scraper up into two asynchronous stages:

1. **Download stage** - The website is crawled, and the pages to
   be scraped are downloaded and saved to disk.
2. **Extract stage** - The pages to be scraped are loaded from disk.
   The desired data is extracted from the pages and exported (e.g. to
   a file or database).

The crawler logic for the download stage should be kept as simple
as possible. It would typically open a known URL and perform very
simple actions such as clicking a "next page" button or submitting
a search query. This reduces the risk of the downloader breaking if
there are minor changes made to the website.

And since all of the raw data is being saved, if you ever decide to
change your extractor logic, you can simply re-run the extractor on
all of the data that has been downloaded.

Installation
=============

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

Whenever you are using `scrapy-twostage`, you should create
two Scrapy spiders - one for the *download* stage and one for
the the *extract* stage. These spiders can either be in the
same Scrapy project, or can be in two separate Scrapy projects.

Let's take the example ``QuotesSpider`` from the `scrapy
documentation <https://doc.scrapy.org/en/1.3/intro/tutorial.html>`_::

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

We should break this up into two Scrapy spiders. Let's call the first one
``QuotesDownloaderSpider`` and the second one ``QuotesExtractorSpider``.

Stage 1: the downloader spider
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The goal of your *downloader* spider is to:

1. Crawl the website, performing whatever actions are required
   to visit every page that needs to be scraped (e.g. clicking
   links, entering search queries)
2. Generate a `DownloadedPage` object corresponding to every page
   that is to be downloaded.

Here is how we might create a downloader spider that corresponds
to the `QuotesSpider`::

    import scrapy


    class QuotesDownloaderSpider(scrapy.Spider):
        name = "quotes"
        start_urls = ['http://quotes.toscrape.com/']

        def parse(self, response):
            yield DownloadedPage.from_response(response)

            next_page_url = response.css("li.next > a::attr(href)").extract_first()
            if next_page_url is not None:
                yield scrapy.Request(response.urljoin(next_page_url))


You should then specify how and where to store the downloaded pages in
your settings. For example::

    FEED_FORMAT = 'pickle'
    FEED_URI = 'file:///path/to/your/files/%(name)s/%(time)s.pickle'

Note: it is essential that the FEED_URI endws with `.pickle`.

Stage 2: the extractor spider
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The extractor spider is responsible for scraping the pages which were
downloaded in stage 1.

Here is how we might create an extractor spider that corresponds
to the `QuotesSpider`::

    import scrapy


    class QuotesExtractorSpider(scrapy.Spider):
        name = "quotes"
        start_urls = ['http://quotes.toscrape.com/']

        def __init__(self):
            super(QuotesExtractorSpider, self).__init__()
            self.response_url_router = (
                (re.compile(r"prospectstampsandcoins.com.au/banknotes/page-"), None),
                (re.compile(r"prospectstampsandcoins.com.au/banknotes/"), self.banknote),
                (re.compile(r"prospectstampsandcoins.com.au/banknote-accessories-and-catalogues/"), None),
                (re.compile(r"prospectstampsandcoins.com.au/royal-australian-mint/"), None),
                (re.compile(r"prospectstampsandcoins.com.au/coin-accessories-and-catalogues/"), None),
                (re.compile(r"prospectstampsandcoins.com.au/anda-coin-fair-releases-en/"), None),
            )



        def parse(self, response):
            for quote in response.css("div.quote"):
                yield {
                    'text': quote.css("span.text::text").extract_first(),
                    'author': quote.css("small.author::text").extract_first(),
                    'tags': quote.css("div.tags > a.tag::text").extract()
                }


blah

Compressed pickle storage
=========================

Put this in your settings::

    FEED_EXPORTERS = {
        'gzip-pickle': 'scrapy_twostage.stage1.GzipPickleItemExporter',
    }
    FEED_FORMAT = 'gzip-pickle'

Also, ensure that your `FEED_URI` ends with the extension `.pickle.gz`.
For example::

    FEED_URI = 'file:///path/to/your/files/%(name)s/%(time)s.pickle.gz'

Storing images
==============

If you also wish to save images, you should enable ITEM_PIPELINES,
something like this::

    ITEM_PIPELINES = {
        'scrapy.pipelines.images.ImagesPipeline': 1,
    }
    IMAGES_THUMBS = {
        'small': (64, 64),
        'large': (256, 256),
    }
    IMAGES_STORE = 's3://%s/_images/' % AWS_BUCKET_NAME

Then you should extract the image URLs and including them in the
`DownloadedPage` object, e.g.::

    def parse(self, response):
        image_urls = response.selector.xpath('//img/@src').extract()
        yield DownloadedPage.from_response(response, image_urls=image_urls)

Using Amazon S3
===============

Just specify your `FEED_URI` as an S3 URI, e.g.::

    FEED_URI = 's3://%s:%s@%s/%%(name)s/%%(time)s.pickle.gz' % (
        AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_BUCKET_NAME
    )

If you are storing images, you can use an S3 URI too::

    IMAGES_STORE = 's3://%s/_images/' % AWS_BUCKET_NAME

Bug tracker
===========

If you have any suggestions, bug reports or annoyances please report them
at http://github.com/acordiner/scrapy-twostage/issues/

License
=======

This software is licensed under the ``GPL v2 License``. See the ``LICENSE``
file in the top distribution directory for the full license text.
