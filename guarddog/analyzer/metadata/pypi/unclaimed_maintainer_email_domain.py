from guarddog.analyzer.metadata.unclaimed_maintainer_email_domain import UnclaimedMaintainerEmailDomainDetector

from .utils import get_email_addresses


class PypiUnclaimedMaintainerEmailDomainDetector(UnclaimedMaintainerEmailDomainDetector):
    def __init__(self):
        super().__init__("pypi")

    def get_email_addresses(self, package_info: dict):
        info = package_info.get("info", {})
        author_email = info.get("author_email")
        if author_email:
            return {author_email}
        maintainer_email = info.get("maintainer_email")
        if maintainer_email:
            return {maintainer_email}
        return set()
