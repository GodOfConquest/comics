from comics.aggregator.crawler import CrawlerBase, CrawlerImage
from comics.meta.base import MetaBase

class Meta(MetaBase):
    name = 'Subnormality'
    language = 'en'
    url = 'http://www.viruscomix.com/subnormality.html'
    start_date = '2007-01-01'
    rights = 'Winston Rowntree'

class Crawler(CrawlerBase):
    history_capable_days = 10000
    time_zone = 1

    def crawl(self, pub_date):
        feed = self.parse_feed('http://www.viruscomix.com/rss.xml')
        for entry in feed.for_date(pub_date):
            page = self.parse_page(entry.link)
            url = page.src('body > img[src$=".jpg"]')
            title = page.text('title')
            return CrawlerImage(url, title)