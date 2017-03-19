import unittest
from StringIO import StringIO

import scrapy
from scrapy.http import Response

from scrapy_twostage.stage1.exporters import GzipPickleItemExporter
from scrapy_twostage.stage1.items import DownloadedPage
from scrapy_twostage.stage2.spiders import PickledResponseSpiderMixin


class PickleItemTestCase(unittest.TestCase):

    def test_export_and_load(self):

        class Stage2Spider(PickledResponseSpiderMixin, scrapy.Spider):
            name = 'stage2spider'

            def __init__(self):
                super(Stage2Spider, self).__init__()
                self.response_url_router = (
                    ('.*/foo', self.parse_foo),
                    ('.*/bar', self.parse_bar),
                )

            def parse_foo(self, response):
                yield {
                    'func': 'parse_foo',
                    'url': response.url,
                    'text': response.text,
                }

            def parse_bar(self, response):
                yield {
                    'func': 'parse_bar',
                    'url': response.url,
                    'text': response.text,
                }

        page1 = DownloadedPage(
            status=200,
            url='http://example.com/foo',
            text='foo',
        )
        page2 = DownloadedPage(
            status=200,
            url='http://example.com/bar',
            text='bar',
        )

        fp = StringIO()

        exporter = GzipPickleItemExporter(fp)
        exporter.export_item(page1)
        exporter.export_item(page2)

        response = Response(
            status=200,
            url='file://temp.pickle.gz',
            body=fp.getvalue(),
        )

        spider = Stage2Spider()
        items = spider.parse(response)
        self.assertDictEqual(next(items), {
            'func': 'parse_foo',
            'url': 'http://example.com/foo',
            'text': 'foo',
        })
        self.assertDictEqual(next(items), {
            'func': 'parse_bar',
            'url': 'http://example.com/bar',
            'text': 'bar',
        })
        with self.assertRaises(StopIteration):
            next(items)
