"""
Web crawler module for fetching job postings from external sites.
"""

from .base import BaseCrawler
from .indeed import IndeedCrawler
from .bossjobs import BossJobsCrawler
from .manager import CrawlerManager 