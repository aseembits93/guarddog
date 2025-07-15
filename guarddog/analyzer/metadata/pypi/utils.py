def get_email_addresses(package_info: dict) -> set[str]:
    info = package_info.get("info", {})
    email = info.get("author_email") or info.get("maintainer_email")
    if email is not None:
        return {email}
    return set()
