"""Aggregator which fetches comic strips from the web"""

import datetime as dt
import logging
import socket

from django.conf import settings

from comics.aggregator.downloader import ComicDownloader
from comics.aggregator.exceptions import StripAlreadyExists
from comics.core.exceptions import ComicsError
from comics.comics import get_comic_module

logger = logging.getLogger('comics.aggregator.command')
socket.setdefaulttimeout(10)

class ComicAggregator(object):
    def __init__(self, config=None, optparse_options=None):
        if config is None and optparse_options is not None:
            self.config = ComicAggregatorConfig(optparse_options)
        else:
            assert isinstance(config, ComicAggregatorConfig)
            self.config = config

    def start(self):
        for comic in self.config.comics:
            self._try_aggregate_one_comic(comic)

    def stop(self):
        pass

    def _try_aggregate_one_comic(self, comic):
        try:
            self._aggregate_one_comic(comic)
        except Exception, error:
            logger.exception(error)

    def _aggregate_one_comic(self, comic):
        crawler = self._get_comic_crawler(comic)
        pub_date = self._get_from_date(comic)
        logger.info('Crawling %s from %s to %s'
            % (comic.slug, pub_date, self.config.to_date))
        while pub_date <= self.config.to_date:
            strip_metadata = self._try_crawl_one_comic_one_date(
                crawler, pub_date)
            if strip_metadata:
                self._try_download_strip(strip_metadata)
            pub_date += dt.timedelta(days=1)

    def _get_comic_crawler(self, comic):
        module = get_comic_module(comic.slug)
        return module.ComicCrawler(comic)

    def _get_from_date(self, comic):
        if self.config.from_date < comic.history_capable():
            logger.info('Adjusting from date to %s because of limited ' +
                'history capability', comic.history_capable())
            return comic.history_capable()
        else:
            return self.config.from_date

    def _try_crawl_one_comic_one_date(self, crawler, pub_date):
        try:
            logger.debug('Crawling %s for %s', crawler.comic.slug, pub_date)
            return self._crawl_one_comic_one_date(crawler, pub_date)
        except ComicsError, error:
            logger.info(error)
        except IOError, error:
            logger.warning(error)
        except Exception, error:
            logger.exception(error)

    def _crawl_one_comic_one_date(self, crawler, pub_date):
        strip_metadata = crawler.get_strip_metadata(pub_date)
        logger.debug('Strip date: %s', strip_metadata['pub_date'])
        logger.debug('Strip URL: %s', strip_metadata['url'])
        logger.debug('Strip title: %s', strip_metadata['title'])
        logger.debug('Strip text: %s', strip_metadata['text'])
        return strip_metadata

    def _try_download_strip(self, strip_metadata):
        try:
            logger.debug('Downloading %s for %s',
                strip_metadata['comic'].slug, strip_metadata['pub_date'])
            downloader = self._get_comic_downloader()
            return self._download_strip(downloader, strip_metadata)
        except ComicsError, error:
            logger.info(error)
        except IOError, error:
            logger.warning(error)
        except Exception, error:
            logger.exception(error)

    def _get_comic_downloader(self):
        return ComicDownloader()

    def _download_strip(self, downloader, strip_metadata):
        downloader.download_strip(strip_metadata)
        logger.info('Strip saved (%s/%s)',
            strip_metadata['comic'].slug, strip_metadata['pub_date'])


class ComicAggregatorConfig(object):
    DATE_FORMAT = '%Y-%m-%d'

    def __init__(self, options=None):
        self.comics = []
        self.from_date = today()
        self.to_date = today()
        if options is not None:
            self.setup(options)

    def setup(self, options):
        self.set_comics_to_crawl(options.get('comic_slugs', None))
        self.set_date_interval(
            options.get('from_date', None),
            options.get('to_date', None))

    def set_comics_to_crawl(self, comic_slugs):
        from comics.core.models import Comic
        if comic_slugs is None or len(comic_slugs) == 0:
            logger.debug('Crawl targets: all comics')
            self.comics = Comic.objects.all()
        else:
            comics = []
            for comic_slug in comic_slugs:
                comics.append(self._get_comic_by_slug(comic_slug))
            logger.debug('Crawl targets: %s' % comics)
            self.comics = comics

    def _get_comic_by_slug(self, comic_slug):
        from comics.core.models import Comic
        try:
            comic = Comic.objects.get(slug=comic_slug)
        except Comic.DoesNotExist:
            error_msg = 'Comic %s not found' % comic_slug
            logger.error(error_msg)
            raise ComicsError(error_msg)
        return comic

    def set_date_interval(self, from_date, to_date):
        self._set_from_date(from_date)
        self._set_to_date(to_date)
        self._validate_dates()

    def _set_from_date(self, from_date):
        if from_date is not None:
            self.from_date = dt.datetime.strptime(
                str(from_date), self.DATE_FORMAT).date()
        logger.debug('From date: %s', self.from_date)

    def _set_to_date(self, to_date):
        if to_date is not None:
            self.to_date = dt.datetime.strptime(
                str(to_date), self.DATE_FORMAT).date()
        logger.debug('To date: %s', self.to_date)

    def _validate_dates(self):
        if self.from_date > self.to_date:
            error_msg = 'From date (%s) after to date (%s)' % (
                self.from_date, self.to_date)
            logger.error(error_msg)
            raise ComicsError(error_msg)
        else:
            return True

# For testability
today = dt.date.today