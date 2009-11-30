from comics.aggregator.crawler import BaseComicCrawler
from comics.meta.base import BaseComicMeta

class ComicMeta(BaseComicMeta):
    name = 'EON'
    language = 'no'
    url = 'http://www.nettavisen.no/tegneserie/striper/'
    start_date = '2008-11-19'
    history_capable_date = '2008-11-19'
    schedule = 'We'
    time_zone = 1
    rights = 'Lars Lauvik'

class ComicCrawler(BaseComicCrawler):
    def crawl(self):
        self.url = 'http://pub.tv2.no/nettavisen/tegneserie/pondus/eon/%(date)s.gif' % {
            'date': self.pub_date.strftime('%d%m%y'),
        }