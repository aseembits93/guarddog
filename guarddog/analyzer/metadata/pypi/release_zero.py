""" Empty Information Detector

Detects when a package has its latest release version to 0.0.0
"""
import logging
from typing import Optional

from guarddog.analyzer.metadata.release_zero import ReleaseZeroDetector

log = logging.getLogger("guarddog")


class PypiReleaseZeroDetector(ReleaseZeroDetector):

    def detect(self, package_info, path: Optional[str] = None, name: Optional[str] = None,
               version: Optional[str] = None) -> tuple[bool, str]:
        version_str = package_info["info"]["version"]  # Avoid repeated dict lookup

        # Only format the debug log message if DEBUG logging is enabled
        if log.isEnabledFor(logging.DEBUG):
            log.debug(
                "Running zero version heuristic on PyPI package %s version %s",
                name, version
            )

        is_zero = version_str in _RELEASE_ZERO_SET  # Set membership is faster than list
        return (
            is_zero,
            ReleaseZeroDetector.MESSAGE_TEMPLATE % version_str
        )

_RELEASE_ZERO_SET = {"0.0.0", "0.0"}
