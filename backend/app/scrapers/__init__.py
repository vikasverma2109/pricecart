"""
Scraper registry. Add new platforms here.

To add a new platform:
1. Create scrapers/<platform>.py subclassing BaseScraper
2. Import it here and add to ALL_SCRAPERS
"""

from .blinkit import BlinkitScraper
from .flipkart import FlipkartScraper
from .amazon import AmazonScraper

ALL_SCRAPERS = [
    BlinkitScraper,
    FlipkartScraper,
    AmazonScraper,
]

__all__ = [
    "ALL_SCRAPERS",
    "BlinkitScraper",
    "FlipkartScraper",
    "AmazonScraper",
]
