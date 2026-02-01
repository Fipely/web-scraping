# -*- coding: utf-8 -*-
"""
Módulo de scrapers.
"""

from scrapers.base_scraper import BaseScraper
from scrapers.references import ReferenceScraper
from scrapers.brands import BrandScraper
from scrapers.models import ModelScraper
from scrapers.values import ValueScraper
from scrapers.orchestrator import Orchestrator

__all__ = [
    "BaseScraper",
    "ReferenceScraper",
    "BrandScraper",
    "ModelScraper",
    "ValueScraper",
    "Orchestrator"
]
