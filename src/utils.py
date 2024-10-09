def match_addresses(address: str, addresses: list[str]) -> bool:
    return address.lower() in [a.lower() for a in addresses]