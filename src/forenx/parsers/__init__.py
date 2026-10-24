"""
Browser artifact parsers package for ForenX.
"""
from forenx.parsers.base import BaseBrowserParser, ParserResult
from forenx.parsers.chromium import ChromiumHistoryParser
from forenx.parsers.firefox import FirefoxPlacesParser

__all__ = ["BaseBrowserParser", "ChromiumHistoryParser", "FirefoxPlacesParser", "ParserResult"]
