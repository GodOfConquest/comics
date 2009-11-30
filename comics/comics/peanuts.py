from comics.aggregator.crawler import BaseComicsComComicCrawler
from comics.meta.base import BaseComicMeta

class ComicMeta(BaseComicMeta):
    name = 'Peanuts'
    language = 'en'
    url = 'http://comics.com/peanuts/'
    start_date = '1950-10-02'
    end_date = '2000-02-13'
    history_capable_date = '1950-10-02'
    schedule = 'Mo,Tu,We,Th,Fr,Sa,Su'
    rights = 'Charles M. Schulz'

class ComicCrawler(BaseComicsComComicCrawler):
    def crawl(self):
        self.crawl_helper('Peanuts')