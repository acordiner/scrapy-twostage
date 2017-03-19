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

Coming soon...

Bug tracker
===========

If you have any suggestions, bug reports or annoyances please report them
at http://github.com/acordiner/scrapy-twostage/issues/

License
=======

This software is licensed under the ``GPL v2 License``. See the ``LICENSE``
file in the top distribution directory for the full license text.
