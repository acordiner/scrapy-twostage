import pickle
import re
from io import BytesIO
from gzip import GzipFile

import boto3
import scrapy
from scrapy.http import TextResponse
from scrapy.http.request import Request
from six.moves.urllib.parse import urlparse, urlunparse


class S3Spider(scrapy.Spider):

    def start_requests(self):
        # This method is a bug fix: http://stackoverflow.com/a/23050437/2113516
        for url in self.start_urls:
            requests = self.make_requests_from_url(url)
            try:
                for request in requests:
                    yield request
            except TypeError:
                yield requests

    def make_requests_from_url(self, url):
        parsed = urlparse(url)
        if parsed.scheme.lower() != 's3':
            return super(S3Spider, self).make_requests_from_url(url)

        bucket = parsed.netloc
        prefix = parsed.path.lstrip('/')

        s3 = boto3.client(
            's3',
            aws_access_key_id=self.settings['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=self.settings['AWS_SECRET_ACCESS_KEY'],
        )
        response = s3.list_objects(
            Bucket=bucket,
            Prefix=prefix,
        )
        return (
            Request(
                url=urlunparse(('s3', bucket, key['Key'], None, None, None)),
            )
            for key in response.get('Contents', ())
        )


class PickledResponseSpiderMixin(object):

    PICKLE_EXTENSION = '.pickle'
    GZIPPED_PICKLE_EXTENSION = '.pickle.gz'

    response_url_router = ()

    def parse(self, response):
        if response.url.endswith(self.PICKLE_EXTENSION):
            is_gzipped = False
        elif response.url.endswith(self.GZIPPED_PICKLE_EXTENSION):
            is_gzipped = True
        else:
            # TODO: raise an exception?
            return
        self.logger.info("Unpickling pickled response: %s", response.url)
        fp = BytesIO(response.body)
        if is_gzipped:
            fp = GzipFile(fileobj=fp)
        while True:
            try:
                response_dict = pickle.load(fp)
            except EOFError:
                break
            ret = self.route_response(response_dict)
            if ret is not None:
                for o in ret:
                    yield o

    def route_response(self, response_dict):
        for url_regex, callback_func in self.response_url_router:
            if not hasattr(url_regex, 'search'):
                url_regex = re.compile(url_regex)
            if url_regex.search(response_dict['url']):
                if callback_func is not None:
                    response = TextResponse(
                        url=response_dict['url'],
                        status=response_dict['status'],
                        headers=response_dict.get('headers'),
                        flags=response_dict.get('flags'),
                        body=response_dict['text'].encode('utf-8'),
                        encoding='utf-8',
                    )
                    response.timestamp = response_dict.get('timestamp')
                    self.logger.debug("Routing result for' %s': %s", response_dict['url'], callback_func)
                    ret = callback_func(response)
                    if ret is not None:
                        for o in ret:
                            yield o
                else:
                    self.logger.debug("Routing result for '%s': ignore this URL", response_dict['url'])
                break
        else:
            raise NotImplementedError("No router defined for URL: %s" % response_dict.get('url'))
