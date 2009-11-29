import datetime as dt
import re
import time

from comics.aggregator.exceptions import *
from comics.aggregator.feedparser import FeedParser
from comics.aggregator.lxmlparser import LxmlParser
from comics.core.models import Release, Strip

class BaseComicCrawler(object):
    # Whether to allow multiple releases per day
    multiple_releases_per_day = False

    # Whether to check the mime type of the strip image when downloading
    check_image_mime_type = True

    # Feed object which is reused when crawling multiple dates
    feed = None
    feed_new = None

    def __init__(self, comic):
        self.comic = comic

    def get_strip_metadata(self, pub_date=None):
        """Get URL of strip from pub_date, or the latest strip"""

        self.pub_date = self._get_date_to_crawl(pub_date)
        self.url = None
        self.title = None
        self.text = None

        self.crawl()

        self._check_strip_url()
        if self.feed:
            self._decode_feed_data()

        return {
            'comic': self.comic,
            'check_image_mime_type': self.check_image_mime_type,
            'pub_date': self.pub_date,
            'url': self.url,
            'title': self.title,
            'text': self.text,
        }

    def _get_date_to_crawl(self, pub_date):
        if pub_date is None:
            pub_date = dt.date.today()

        if not self.comic.history_capable() and pub_date != dt.date.today():
            raise NotHistoryCapable

        if (self.comic.history_capable() and
                pub_date < self.comic.history_capable()):
            raise OutsideHistoryCapabilityRange(
                'Not history capable, less than %s' %
                self.comic.history_capable())

        if not self.multiple_releases_per_day:
            if Release.objects.filter(comic=self.comic,
                    pub_date=pub_date).count():
                raise StripAlreadyExists('%s/%s' % (self.comic.slug, pub_date))

        return pub_date

    def _check_strip_url(self):
        """Validate strip URL found by the crawler"""

        if not self.url:
            raise StripURLNotFound('%s/%s' % (self.comic.slug, self.pub_date))

    def _decode_feed_data(self):
        """Decode titles and text retrieved from a feed"""

        if self.feed.encoding and self.feed.encoding != 'utf-8':
            if self.title and type(self.title) != unicode:
                self.title = unicode(self.title, self.feed.encoding)
            if self.text and type(self.text) != unicode:
                self.text = unicode(self.text, self.feed.encoding)

    def crawl(self):
        """Must be overridden by classes inheriting from this one"""

        raise NotImplementedError

    ### Helpers for the crawl() implementations

    def parse_feed(self, feed_url):
        # Cache feed object as it can be reused for multiple dates
        if self.feed_new is None:
            self.feed_new = FeedParser(feed_url)
        # XXX Temporary backwards compatability
        if self.feed is None:
            self.feed = self.feed_new.raw_feed
        return self.feed_new

    def parse_page(self, page_url):
        return LxmlParser(page_url)

    def timestamp_to_date(self, timestamp):
        return dt.date(*timestamp[:3])

    def string_to_date(self, *args, **kwargs):
        return dt.datetime.strptime(*args, **kwargs).date()

    def date_to_epoch(self, date):
        return int(time.mktime(date.timetuple()))

    def remove_html_tags(self, data):
        p = re.compile(r'<[^<]*?>')
        return p.sub('', data)


class BaseComicsComComicCrawler(BaseComicCrawler):
    """Base comic crawler for all comics hosted at comics.com"""

    check_image_mime_type = False

    def crawl_helper(self, comics_com_title):
        page_url = 'http://comics.com/%(slug)s/%(date)s/' % {
            'slug': comics_com_title.lower().replace(' ', '_'),
            'date': self.pub_date.strftime('%Y-%m-%d'),
        }
        page = self.parse_page(page_url)
        self.url = page.src('a.STR_StripImage img[alt^="%s"]' %
            comics_com_title)
