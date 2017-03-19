import gzip
import pickle

from scrapy.exporters import PickleItemExporter


class GzipPickleItemExporter(PickleItemExporter):

    def export_item(self, item):
        d = dict(self._get_serialized_fields(item))
        with gzip.GzipFile(fileobj=self.file, mode='wb') as gzip_fp:
            pickle.dump(d, gzip_fp, self.protocol)
