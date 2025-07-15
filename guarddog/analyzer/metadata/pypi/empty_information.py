""" Empty Information Detector

Detects if a package contains an empty description
"""
import logging
from typing import Optional

from guarddog.analyzer.metadata.empty_information import EmptyInfoDetector

MESSAGE = "This package has an empty description on PyPi"

log = logging.getLogger("guarddog")


class PypiEmptyInfoDetector(EmptyInfoDetector):
    def detect(self, package_info, path: Optional[str] = None, name: Optional[str] = None,
               version: Optional[str] = None) -> tuple[bool, str]:
        # Use lazy logging to avoid formatting cost if debug is not enabled
        log.debug("Running PyPI empty description heuristic on package %s version %s", name, version)
        description = package_info["info"]["description"]
        return len(description.strip()) == 0, EmptyInfoDetector.MESSAGE_TEMPLATE % "PyPI"
